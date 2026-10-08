from ..models import (
    db, Order, OrderStatus, FulfillmentType, PaymentStatus, 
    OrderStatusHistory, PrescriptionReviewStatus, Inventory
)

class OrderTransitionError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class StockConflictError(Exception):
    def __init__(self, message: str = "Requested quantity is no longer available."):
        super().__init__(message)
        self.message = message
        self.status_code = 409


def validate_status_transition(order: Order, new_status: str) -> None:
    """
    Enforce strict status transition rules based on fulfillment type.
    Raises OrderTransitionError if transition is invalid.
    """
    current_status = order.status
    fulfillment = order.fulfillment_type

    # Terminal states cannot be changed
    if current_status in [OrderStatus.COMPLETED, OrderStatus.REJECTED]:
        raise OrderTransitionError(
            f"Cannot change status. Order #{order.id} is already in terminal state '{current_status}'.",
            status_code=400
        )

    # General transition graph
    allowed_transitions = {
        OrderStatus.PLACED: [OrderStatus.ACCEPTED, OrderStatus.REJECTED],
        OrderStatus.ACCEPTED: [OrderStatus.PREPARING],
    }

    # Fulfillment-specific transitions from PREPARING onwards
    if fulfillment == FulfillmentType.PICKUP:
        allowed_transitions[OrderStatus.PREPARING] = [OrderStatus.READY_FOR_PICKUP]
        allowed_transitions[OrderStatus.READY_FOR_PICKUP] = [OrderStatus.COMPLETED]
    elif fulfillment == FulfillmentType.DELIVERY:
        allowed_transitions[OrderStatus.PREPARING] = [OrderStatus.OUT_FOR_DELIVERY]
        allowed_transitions[OrderStatus.OUT_FOR_DELIVERY] = [OrderStatus.COMPLETED]

    # Check validity
    valid_next = allowed_transitions.get(current_status, [])
    if new_status not in valid_next:
        if fulfillment == FulfillmentType.PICKUP and new_status == OrderStatus.OUT_FOR_DELIVERY:
            raise OrderTransitionError("Pickup orders cannot be marked as OUT_FOR_DELIVERY.", status_code=400)
        if fulfillment == FulfillmentType.DELIVERY and new_status == OrderStatus.READY_FOR_PICKUP:
            raise OrderTransitionError("Delivery orders cannot be marked as READY_FOR_PICKUP.", status_code=400)
        
        raise OrderTransitionError(
            f"Invalid status transition from '{current_status}' to '{new_status}' for fulfillment type '{fulfillment}'.",
            status_code=400
        )


def accept_order_with_stock_deduction(order: Order, changed_by_user_id: int) -> Order:
    """
    Accept order safely inside an atomic transaction:
    1. Check prescription requirement and approval
    2. Check stock availability for all order items
    3. Atomically deduct stock
    4. Transition order status to ACCEPTED
    5. Record status history
    """
    # 1. Prescription check
    if order.prescription:
        if order.prescription.review_status != PrescriptionReviewStatus.APPROVED:
            raise OrderTransitionError(
                "Cannot accept order. The uploaded prescription must be APPROVED before acceptance.",
                status_code=400
            )

    # 2 & 3. Atomic stock check and deduction for each item
    for item in order.items:
        # Atomic update with WHERE condition ensuring quantity >= requested
        # Using db.session.query / execute for safe row-level atomic decrement
        inventory_item = Inventory.query.filter_by(
            pharmacy_id=order.pharmacy_id,
            medicine_id=item.medicine_id
        ).first()

        if not inventory_item:
            db.session.rollback()
            raise StockConflictError("Medicine is not available in pharmacy inventory.")

        if inventory_item.quantity < item.quantity:
            db.session.rollback()
            raise StockConflictError("Requested quantity is no longer available.")

        # Decrement quantity atomically
        inventory_item.quantity -= item.quantity
        inventory_item.sync_stock_status()

    # 4. Update order state
    old_status = order.status
    order.status = OrderStatus.ACCEPTED
    
    # 5. Record status history
    history = OrderStatusHistory(
        order_id=order.id,
        old_status=old_status,
        new_status=OrderStatus.ACCEPTED,
        changed_by=changed_by_user_id
    )
    db.session.add(history)
    db.session.commit()

    return order


def update_order_status(order: Order, new_status: str, changed_by_user_id: int) -> Order:
    """
    Transition order status following strict lifecycle rules.
    """
    validate_status_transition(order, new_status)

    if new_status == OrderStatus.ACCEPTED:
        return accept_order_with_stock_deduction(order, changed_by_user_id)

    old_status = order.status
    order.status = new_status

    # If completed, cash payment is fulfilled
    if new_status == OrderStatus.COMPLETED:
        order.payment_status = PaymentStatus.PAID

    history = OrderStatusHistory(
        order_id=order.id,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by_user_id
    )
    db.session.add(history)
    db.session.commit()

    return order
