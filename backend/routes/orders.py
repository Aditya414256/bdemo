import json
from flask import Blueprint, request
from ..models import (
    db, UserRole, Order, OrderItem, OrderStatus, FulfillmentType,
    PaymentMethod, PaymentStatus, OrderStatusHistory, Pharmacy,
    PharmacyVerificationStatus, Medicine, Inventory, Prescription,
    PrescriptionReviewStatus
)
from ..utils.auth import roles_required, get_current_user
from ..utils.file_upload import save_prescription_file
from ..utils.responses import api_response

orders_bp = Blueprint('orders', __name__, url_prefix='/api/orders')

@orders_bp.route('', methods=['POST'])
@roles_required(UserRole.CUSTOMER)
def create_order():
    """
    Create a new customer order.
    Accepts multipart/form-data for prescription upload support.
    """
    current_user = get_current_user()

    # Support both multipart form-data and json
    if request.is_json:
        req_data = request.get_json() or {}
        form_data = req_data
        files = {}
    else:
        form_data = request.form
        files = request.files

    try:
        pharmacy_id = int(form_data.get('pharmacy_id'))
    except (TypeError, ValueError):
        return api_response(False, "A valid pharmacy_id is required.", status_code=400)

    fulfillment_type = (form_data.get('fulfillment_type') or form_data.get('fulfillment_method') or FulfillmentType.PICKUP).strip().upper()
    payment_method = form_data.get('payment_method', PaymentMethod.CASH).strip().upper()
    customer_phone = form_data.get('customer_phone', current_user.phone or '').strip()
    delivery_address = form_data.get('delivery_address', '').strip()
    notes = form_data.get('notes', '').strip()

    # 1. Validate payment method
    if payment_method != PaymentMethod.CASH:
        return api_response(False, "Only CASH payment is supported (Cash on Pickup / Cash on Delivery).", status_code=400)

    # 2. Validate fulfillment type
    if fulfillment_type not in FulfillmentType.CHOICES:
        return api_response(False, f"Invalid fulfillment type. Choose from: {', '.join(FulfillmentType.CHOICES)}.", status_code=400)

    # 3. Validate delivery address if DELIVERY
    if fulfillment_type == FulfillmentType.DELIVERY and not delivery_address:
        return api_response(False, "Delivery address is required for Home Delivery orders.", status_code=400)

    # 4. Validate pharmacy exists and is active + approved
    pharmacy = db.session.get(Pharmacy, pharmacy_id)
    if not pharmacy:
        return api_response(False, "Selected pharmacy does not exist.", status_code=404)
    if not pharmacy.is_active or pharmacy.verification_status != PharmacyVerificationStatus.APPROVED:
        return api_response(False, "Selected pharmacy is not currently available or approved.", status_code=400)

    if fulfillment_type == FulfillmentType.PICKUP and not pharmacy.supports_pickup:
        return api_response(False, "This pharmacy does not support store pickup.", status_code=400)
    if fulfillment_type == FulfillmentType.DELIVERY and not pharmacy.supports_delivery:
        return api_response(False, "This pharmacy does not support home delivery.", status_code=400)

    # 5. Parse order items
    raw_items = form_data.get('items')
    items_to_order = []

    if raw_items:
        if isinstance(raw_items, str):
            try:
                items_to_order = json.loads(raw_items)
            except Exception:
                return api_response(False, "Invalid JSON format for items.", status_code=400)
        elif isinstance(raw_items, list):
            items_to_order = raw_items
    else:
        # Check single item shortcut
        med_id = form_data.get('medicine_id')
        qty = form_data.get('quantity', 1)
        if med_id:
            try:
                items_to_order = [{'medicine_id': int(med_id), 'quantity': int(qty)}]
            except ValueError:
                return api_response(False, "Invalid medicine_id or quantity.", status_code=400)

    if not items_to_order or not isinstance(items_to_order, list):
        return api_response(False, "Order must include at least one medicine item.", status_code=400)

    # 6. Validate items against pharmacy inventory and check prescription requirements
    total_amount = 0.0
    order_items_records = []
    requires_prescription_flag = False

    for item_data in items_to_order:
        try:
            m_id = int(item_data.get('medicine_id'))
            qty = int(item_data.get('quantity', 1))
        except (TypeError, ValueError):
            return api_response(False, "Invalid medicine_id or quantity in items list.", status_code=400)

        if qty <= 0:
            return api_response(False, "Item quantity must be greater than zero.", status_code=400)

        medicine = db.session.get(Medicine, m_id)
        if not medicine:
            return api_response(False, f"Medicine with ID {m_id} not found.", status_code=404)

        inventory_item = Inventory.query.filter_by(pharmacy_id=pharmacy_id, medicine_id=m_id).first()
        if not inventory_item or inventory_item.quantity < qty:
            return api_response(
                False, 
                f"Requested medicine '{medicine.name}' is out of stock or insufficient quantity at selected pharmacy.",
                status_code=400
            )

        if medicine.requires_prescription:
            requires_prescription_flag = True

        unit_price = inventory_item.price
        subtotal = round(unit_price * qty, 2)
        total_amount += subtotal

        order_items_records.append({
            'medicine_id': m_id,
            'quantity': qty,
            'unit_price': unit_price
        })

    # 7. Validate prescription file if required
    prescription_file = files.get('prescription')
    prescription_saved_info = None

    if requires_prescription_flag:
        if not prescription_file or prescription_file.filename == '':
            return api_response(
                False,
                "A prescription upload is required for one or more medicines in your order.",
                status_code=400
            )
        try:
            stored_filename, orig_name, file_type = save_prescription_file(prescription_file)
            prescription_saved_info = {
                'file_path': stored_filename,
                'original_filename': orig_name,
                'file_type': file_type
            }
        except ValueError as e:
            return api_response(False, str(e), status_code=400)
    elif prescription_file and prescription_file.filename != '':
        try:
            stored_filename, orig_name, file_type = save_prescription_file(prescription_file)
            prescription_saved_info = {
                'file_path': stored_filename,
                'original_filename': orig_name,
                'file_type': file_type
            }
        except ValueError as e:
            return api_response(False, str(e), status_code=400)

    # 8. Create Order (Stock is NOT reduced on PLACED)
    new_order = Order(
        customer_id=current_user.id,
        pharmacy_id=pharmacy_id,
        status=OrderStatus.PLACED,
        fulfillment_type=fulfillment_type,
        payment_method=payment_method,
        payment_status=PaymentStatus.PENDING,
        delivery_address=delivery_address if fulfillment_type == FulfillmentType.DELIVERY else None,
        customer_phone=customer_phone if customer_phone else None,
        notes=notes if notes else None,
        total_amount=round(total_amount, 2)
    )
    db.session.add(new_order)
    db.session.flush()

    # 9. Create Order Items
    for oi in order_items_records:
        item_row = OrderItem(
            order_id=new_order.id,
            medicine_id=oi['medicine_id'],
            quantity=oi['quantity'],
            unit_price=oi['unit_price']
        )
        db.session.add(item_row)

    # 10. Create Prescription record if uploaded
    if prescription_saved_info:
        presc_row = Prescription(
            order_id=new_order.id,
            customer_id=current_user.id,
            file_path=prescription_saved_info['file_path'],
            original_filename=prescription_saved_info['original_filename'],
            file_type=prescription_saved_info['file_type'],
            review_status=PrescriptionReviewStatus.PENDING
        )
        db.session.add(presc_row)

    # 11. Record Order Status History
    history = OrderStatusHistory(
        order_id=new_order.id,
        old_status=None,
        new_status=OrderStatus.PLACED,
        changed_by=current_user.id
    )
    db.session.add(history)

    db.session.commit()

    return api_response(
        True,
        "Order placed.",
        data=new_order.to_dict(include_items=True, include_pharmacy=True),
        status_code=201
    )


@orders_bp.route('', methods=['GET'])
@roles_required(UserRole.CUSTOMER)
def get_my_orders():
    """Retrieve all orders placed by the authenticated customer."""
    current_user = get_current_user()
    orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.created_at.desc()).all()

    return api_response(
        True,
        "Orders retrieved successfully.",
        data={'orders': [order.to_dict(include_items=True, include_pharmacy=True) for order in orders]},
        status_code=200
    )


@orders_bp.route('/<int:order_id>', methods=['GET'])
@roles_required(UserRole.CUSTOMER)
def get_order_by_id(order_id: int):
    """Retrieve details and real-time status of a specific customer order."""
    current_user = get_current_user()
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first()

    if not order:
        return api_response(False, "Order not found or unauthorized access.", status_code=404)

    return api_response(
        True,
        order.get_customer_message(),
        data=order.to_dict(include_items=True, include_pharmacy=True),
        status_code=200
    )
