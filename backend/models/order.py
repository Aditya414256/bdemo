from datetime import datetime, timezone
from . import db

class OrderStatus:
    PLACED = "PLACED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    PREPARING = "PREPARING"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    COMPLETED = "COMPLETED"

    CUSTOMER_MESSAGES = {
        PLACED: "Your order has been placed.",
        ACCEPTED: "Your order has been confirmed.",
        PREPARING: "Your order is being prepared.",
        READY_FOR_PICKUP: "Your order is ready for pickup.",
        OUT_FOR_DELIVERY: "Your order is out for delivery.",
        COMPLETED: "Your order has been completed.",
        REJECTED: "Your order was not taken."
    }

    ALL_STATUSES = [
        PLACED, ACCEPTED, REJECTED, PREPARING,
        READY_FOR_PICKUP, OUT_FOR_DELIVERY, COMPLETED
    ]


class FulfillmentType:
    PICKUP = "PICKUP"
    DELIVERY = "DELIVERY"
    CHOICES = [PICKUP, DELIVERY]


class PaymentMethod:
    CASH = "CASH"
    CHOICES = [CASH]


class PaymentStatus:
    PENDING = "PENDING"
    PAID = "PAID"
    CHOICES = [PENDING, PAID]


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id', ondelete='RESTRICT'), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default=OrderStatus.PLACED, index=True)
    fulfillment_type = db.Column(db.String(20), nullable=False, default=FulfillmentType.PICKUP)
    payment_method = db.Column(db.String(20), nullable=False, default=PaymentMethod.CASH)
    payment_status = db.Column(db.String(20), nullable=False, default=PaymentStatus.PENDING)
    delivery_address = db.Column(db.Text, nullable=True)
    customer_phone = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(
        db.DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    prescription = db.relationship('Prescription', backref='order', uselist=False, lazy=True, cascade='all, delete-orphan')
    status_history = db.relationship('OrderStatusHistory', backref='order', lazy=True, order_by='OrderStatusHistory.changed_at.asc()', cascade='all, delete-orphan')

    def get_customer_message(self) -> str:
        """Return standardized user-facing status message."""
        return OrderStatus.CUSTOMER_MESSAGES.get(self.status, "Order updated.")

    def to_dict(self, include_items=True, include_pharmacy=True, include_customer=False):
        """Serialize order details to dictionary."""
        data = {
            'id': self.id,
            'customer_id': self.customer_id,
            'pharmacy_id': self.pharmacy_id,
            'status': self.status,
            'status_message': self.get_customer_message(),
            'fulfillment_type': self.fulfillment_type,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'delivery_address': self.delivery_address,
            'customer_phone': self.customer_phone,
            'notes': self.notes,
            'total_amount': self.total_amount,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'has_prescription': self.prescription is not None,
            'prescription_status': self.prescription.review_status if self.prescription else None
        }

        if include_pharmacy and self.pharmacy:
            data['pharmacy'] = {
                'id': self.pharmacy.id,
                'name': self.pharmacy.name,
                'phone': self.pharmacy.phone,
                'address': self.pharmacy.address,
                'city': self.pharmacy.city,
                'pincode': self.pharmacy.pincode
            }

        if include_customer and self.customer:
            data['customer'] = {
                'id': self.customer.id,
                'name': self.customer.name,
                'email': self.customer.email,
                'phone': self.customer.phone
            }

        if include_items:
            data['items'] = [item.to_dict() for item in self.items]

        return data


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id', ondelete='RESTRICT'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)

    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='check_order_item_quantity_positive'),
        db.CheckConstraint('unit_price >= 0', name='check_order_item_unit_price_non_negative'),
    )

    def to_dict(self):
        """Serialize order item."""
        data = {
            'id': self.id,
            'order_id': self.order_id,
            'medicine_id': self.medicine_id,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'subtotal': round(self.quantity * self.unit_price, 2)
        }
        if self.medicine:
            data['medicine_name'] = self.medicine.name
            data['dosage_form'] = self.medicine.dosage_form
            data['strength'] = self.medicine.strength
            data['requires_prescription'] = self.medicine.requires_prescription
        return data


class OrderStatusHistory(db.Model):
    __tablename__ = 'order_status_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    old_status = db.Column(db.String(30), nullable=True)
    new_status = db.Column(db.String(30), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    changed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        """Serialize status transition entry."""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'changed_by': self.changed_by,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None
        }
