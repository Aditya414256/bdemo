from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, request, send_file, current_app
from ..models import (
    db, UserRole, Order, OrderStatus, OrderStatusHistory,
    Pharmacy, Medicine, Inventory, Prescription, PrescriptionReviewStatus,
    PharmacyVerificationStatus
)
from ..services.order_service import update_order_status, OrderTransitionError, StockConflictError
from ..utils.auth import roles_required, get_current_user
from ..utils.file_upload import get_prescription_full_path
from ..utils.responses import api_response

pharmacy_bp = Blueprint('pharmacy', __name__, url_prefix='/api/pharmacy')

def _get_owner_pharmacy():
    """Helper to retrieve pharmacy owned by current authenticated user."""
    current_user = get_current_user()
    pharmacy = Pharmacy.query.filter_by(owner_id=current_user.id).first()
    return pharmacy


# --- Public Pharmacy Listing ---

@pharmacy_bp.route('', methods=['GET'])
@pharmacy_bp.route('/list', methods=['GET'])
def get_all_verified_pharmacies():
    """Public endpoint to list verified active pharmacies."""
    pharmacies = Pharmacy.query.filter_by(
        is_active=True,
        verification_status=PharmacyVerificationStatus.APPROVED
    ).all()
    return api_response(
        True,
        f"Retrieved {len(pharmacies)} verified pharmacies.",
        data={'pharmacies': [p.to_dict() for p in pharmacies]},
        status_code=200
    )


# --- Owner Profile ---

@pharmacy_bp.route('/profile', methods=['GET'])
@roles_required(UserRole.PHARMACY_OWNER)
def get_owner_pharmacy_profile():
    """Retrieve pharmacy profile for the logged in owner."""
    pharmacy = _get_owner_pharmacy()
    if not pharmacy:
        return api_response(False, "Pharmacy profile not found for this user.", status_code=404)
    return api_response(
        True,
        "Pharmacy profile retrieved.",
        data=pharmacy.to_dict(include_owner=True),
        status_code=200
    )


# --- Orders Management ---

@pharmacy_bp.route('/orders', methods=['GET'])
@roles_required(UserRole.PHARMACY_OWNER)
def get_pharmacy_orders():
    """List all orders received by the logged-in owner's pharmacy."""
    pharmacy = _get_owner_pharmacy()
    if not pharmacy:
        return api_response(False, "Pharmacy profile not found for this user.", status_code=404)

    status_filter = request.args.get('status')
    query = Order.query.filter_by(pharmacy_id=pharmacy.id)
    if status_filter:
        query = query.filter_by(status=status_filter.upper())

    orders = query.order_by(Order.created_at.desc()).all()

    return api_response(
        True,
        "Pharmacy orders retrieved successfully.",
        data={
            'pharmacy_id': pharmacy.id,
            'orders': [o.to_dict(include_items=True, include_pharmacy=False, include_customer=True) for o in orders]
        },
        status_code=200
    )


@pharmacy_bp.route('/orders/<int:order_id>', methods=['GET'])
@roles_required(UserRole.PHARMACY_OWNER)
def get_pharmacy_order_details(order_id: int):
    """Retrieve full details of an order belonging to the owner's pharmacy."""
    pharmacy = _get_owner_pharmacy()
    if not pharmacy:
        return api_response(False, "Pharmacy profile not found for this user.", status_code=404)

    order = Order.query.filter_by(id=order_id, pharmacy_id=pharmacy.id).first()
    if not order:
        return api_response(False, "Order not found or unauthorized.", status_code=404)

    return api_response(
        True,
        "Order details retrieved.",
        data=order.to_dict(include_items=True, include_pharmacy=False, include_customer=True),
        status_code=200
    )


@pharmacy_bp.route('/orders/<int:order_id>/status', methods=['PATCH'])
@roles_required(UserRole.PHARMACY_OWNER)
def update_order_status_route(order_id: int):
    """
    Update order status according to strict transition workflow.
    Body: { "status": "ACCEPTED" | "REJECTED" | "PREPARING" | ... }
    """
    pharmacy = _get_owner_pharmacy()
    if not pharmacy:
        return api_response(False, "Pharmacy profile not found for this user.", status_code=404)

    order = Order.query.filter_by(id=order_id, pharmacy_id=pharmacy.id).first()
    if not order:
        return api_response(False, "Order not found or unauthorized.", status_code=404)

    data = request.get_json() or {}
    new_status = data.get('status', '').strip().upper()
    if not new_status:
        return api_response(False, "Target status is required.", status_code=400)

    current_user = get_current_user()

    try:
        updated_order = update_order_status(order, new_status, current_user.id)
        return api_response(
            True,
            f"Order #{order.id} status updated to {updated_order.status}.",
            data=updated_order.to_dict(include_items=True, include_pharmacy=False, include_customer=True),
            status_code=200
        )
    except OrderTransitionError as e:
        return api_response(False, e.message, status_code=e.status_code)
    except StockConflictError as e:
        return api_response(False, e.message, status_code=e.status_code)


# --- Prescription Review & Secure Access ---

@pharmacy_bp.route('/orders/<int:order_id>/prescription', methods=['GET'])
@roles_required(UserRole.PHARMACY_OWNER)
def view_order_prescription(order_id: int):
    """Securely access the uploaded prescription file for an authorized pharmacy order."""
    pharmacy = _get_owner_pharmacy()
    if not pharmacy:
        return api_response(False, "Pharmacy profile not found for this user.", status_code=404)

    order = Order.query.filter_by(id=order_id, pharmacy_id=pharmacy.id).first()
    if not order or not order.prescription:
        return api_response(False, "Prescription not found for this order.", status_code=404)

    file_full_path = get_prescription_full_path(order.prescription.file_path)

    if not file_full_path.exists():
        return api_response(False, "Prescription file does not exist on storage.", status_code=404)

    return send_file(
        str(file_full_path),
        mimetype=order.prescription.file_type,
        as_attachment=False,
        download_name=order.prescription.original_filename
    )


@pharmacy_bp.route('/orders/<int:order_id>/prescription', methods=['PATCH'])
@roles_required(UserRole.PHARMACY_OWNER)
def review_order_prescription(order_id: int):
    """
    Approve or reject a prescription for an order.
    Body: { "status": "APPROVED" | "REJECTED" }
    If rejected, the order is also rejected.
    """
    pharmacy = _get_owner_pharmacy()
    if not pharmacy:
        return api_response(False, "Pharmacy profile not found for this user.", status_code=404)

    order = Order.query.filter_by(id=order_id, pharmacy_id=pharmacy.id).first()
    if not order or not order.prescription:
        return api_response(False, "Prescription not found for this order.", status_code=404)

    data = request.get_json() or {}
    review_status = data.get('status', '').strip().upper()

    if review_status not in [PrescriptionReviewStatus.APPROVED, PrescriptionReviewStatus.REJECTED]:
        return api_response(False, "Review status must be either APPROVED or REJECTED.", status_code=400)

    current_user = get_current_user()
    order.prescription.review_status = review_status
    order.prescription.reviewed_by = current_user.id
    order.prescription.reviewed_at = datetime.now(timezone.utc)

    if review_status == PrescriptionReviewStatus.REJECTED:
        old_status = order.status
        order.status = OrderStatus.REJECTED
        history = OrderStatusHistory(
            order_id=order.id,
            old_status=old_status,
            new_status=OrderStatus.REJECTED,
            changed_by=current_user.id
        )
        db.session.add(history)

    db.session.commit()

    return api_response(
        True,
        f"Prescription has been {review_status.lower()}.",
        data={
            'order_id': order.id,
            'order_status': order.status,
            'prescription': order.prescription.to_dict()
        },
        status_code=200
    )


# --- Inventory Management ---

@pharmacy_bp.route('/inventory', methods=['GET'])
@roles_required(UserRole.PHARMACY_OWNER)
def get_pharmacy_inventory():
    """List inventory items for the authenticated pharmacy owner."""
    pharmacy = _get_owner_pharmacy()
    if not pharmacy:
        return api_response(False, "Pharmacy profile not found for this user.", status_code=404)

    inventory_items = Inventory.query.filter_by(pharmacy_id=pharmacy.id).all()
    return api_response(
        True,
        "Inventory retrieved successfully.",
        data={'inventory': [item.to_dict(include_medicine=True) for item in inventory_items]},
        status_code=200
    )


@pharmacy_bp.route('/inventory', methods=['POST'])
@roles_required(UserRole.PHARMACY_OWNER)
def add_inventory_item():
    """
    Add an existing medicine to the pharmacy's inventory.
    Body: { "medicine_id": 1, "quantity": 10, "price": 50.0 }
    """
    pharmacy = _get_owner_pharmacy()
    if not pharmacy:
        return api_response(False, "Pharmacy profile not found for this user.", status_code=404)

    data = request.get_json() or {}
    try:
        medicine_id = int(data.get('medicine_id'))
        quantity = int(data.get('quantity', 0))
        price = float(data.get('price', 0.0))
    except (TypeError, ValueError):
        return api_response(False, "Valid medicine_id, quantity, and price are required.", status_code=400)

    if quantity < 0:
        return api_response(False, "Quantity cannot be negative.", status_code=400)
    if price < 0:
        return api_response(False, "Price cannot be negative.", status_code=400)

    medicine = db.session.get(Medicine, medicine_id)
    if not medicine:
        return api_response(False, "Medicine not found in catalog. Owners cannot create new medicines.", status_code=404)

    existing_inv = Inventory.query.filter_by(pharmacy_id=pharmacy.id, medicine_id=medicine_id).first()
    if existing_inv:
        return api_response(False, "This medicine is already in your inventory. Use PATCH to update stock/price.", status_code=409)

    new_inv = Inventory(
        pharmacy_id=pharmacy.id,
        medicine_id=medicine_id,
        quantity=quantity,
        price=price,
        stock_status='IN_STOCK' if quantity > 0 else 'OUT_OF_STOCK'
    )
    db.session.add(new_inv)
    db.session.commit()

    return api_response(
        True,
        f"Added '{medicine.name}' to inventory.",
        data=new_inv.to_dict(include_medicine=True),
        status_code=201
    )


@pharmacy_bp.route('/inventory/<int:inventory_id>', methods=['PATCH'])
@roles_required(UserRole.PHARMACY_OWNER)
def update_inventory_item(inventory_id: int):
    """
    Update stock quantity and/or price for an existing inventory item.
    Body: { "quantity": 25, "price": 45.0 }
    """
    pharmacy = _get_owner_pharmacy()
    if not pharmacy:
        return api_response(False, "Pharmacy profile not found for this user.", status_code=404)

    inv = Inventory.query.filter_by(id=inventory_id, pharmacy_id=pharmacy.id).first()
    if not inv:
        return api_response(False, "Inventory item not found or unauthorized.", status_code=404)

    data = request.get_json() or {}

    if 'quantity' in data:
        try:
            qty = int(data['quantity'])
            if qty < 0:
                return api_response(False, "Quantity cannot be negative.", status_code=400)
            inv.quantity = qty
            inv.sync_stock_status()
        except ValueError:
            return api_response(False, "Invalid quantity format.", status_code=400)

    if 'price' in data:
        try:
            price = float(data['price'])
            if price < 0:
                return api_response(False, "Price cannot be negative.", status_code=400)
            inv.price = price
        except ValueError:
            return api_response(False, "Invalid price format.", status_code=400)

    db.session.commit()

    return api_response(
        True,
        "Inventory item updated.",
        data=inv.to_dict(include_medicine=True),
        status_code=200
    )
