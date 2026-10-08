import io
import json
from backend.models import db, Inventory, Order, OrderStatus, PaymentStatus, PrescriptionReviewStatus

def test_pharmacy_isolation(client, auth_tokens):
    """Ensure pharmacy owner 2 cannot view or modify pharmacy 1 orders."""
    # Place order for Pharmacy 1
    create_res = client.post(
        '/api/orders',
        headers={'Authorization': f"Bearer {auth_tokens['customer']}"},
        data={
            'pharmacy_id': 1,
            'fulfillment_type': 'PICKUP',
            'payment_method': 'CASH',
            'items': json.dumps([{'medicine_id': 1, 'quantity': 1}])
        }
    )
    order_id = create_res.get_json()['data']['id']

    # Pharmacy Owner 1 can see it
    res1 = client.get(f'/api/pharmacy/orders/{order_id}', headers={'Authorization': f"Bearer {auth_tokens['owner1']}"})
    assert res1.status_code == 200

    # Pharmacy Owner 2 gets 404 / unauthorized
    res2 = client.get(f'/api/pharmacy/orders/{order_id}', headers={'Authorization': f"Bearer {auth_tokens['owner2']}"})
    assert res2.status_code == 404


def test_prescription_approval_and_order_acceptance(client, auth_tokens, app):
    """Test full prescription review, atomic stock deduction, and order acceptance."""
    # 1. Customer places order with prescription
    prescription_data = (io.BytesIO(b"Sample PDF Prescription"), 'rx.pdf')
    order_res = client.post(
        '/api/orders',
        headers={'Authorization': f"Bearer {auth_tokens['customer']}"},
        data={
            'pharmacy_id': 1,
            'fulfillment_type': 'PICKUP',
            'payment_method': 'CASH',
            'items': json.dumps([{'medicine_id': 2, 'quantity': 2}]), # 2 x Amoxicillin
            'prescription': prescription_data
        },
        content_type='multipart/form-data'
    )
    order_id = order_res.get_json()['data']['id']

    # Initial stock of Amoxicillin at Pharmacy 1 is 5
    with app.app_context():
        inv_before = Inventory.query.filter_by(pharmacy_id=1, medicine_id=2).first().quantity
        assert inv_before == 5

    # 2. Owner tries to accept order while prescription is PENDING -> Should FAIL
    accept_attempt = client.patch(
        f'/api/pharmacy/orders/{order_id}/status',
        headers={'Authorization': f"Bearer {auth_tokens['owner1']}"},
        json={'status': 'ACCEPTED'}
    )
    assert accept_attempt.status_code == 400
    assert "prescription must be approved" in accept_attempt.get_json()['message'].lower()

    # 3. Owner views prescription file securely
    presc_view = client.get(
        f'/api/pharmacy/orders/{order_id}/prescription',
        headers={'Authorization': f"Bearer {auth_tokens['owner1']}"}
    )
    assert presc_view.status_code == 200

    # 4. Owner APPROVES prescription
    review_res = client.patch(
        f'/api/pharmacy/orders/{order_id}/prescription',
        headers={'Authorization': f"Bearer {auth_tokens['owner1']}"},
        json={'status': 'APPROVED'}
    )
    assert review_res.status_code == 200
    assert review_res.get_json()['data']['prescription']['review_status'] == 'APPROVED'

    # 5. Owner accepts order -> Should SUCCEED and DEDUCT stock atomically
    accept_res = client.patch(
        f'/api/pharmacy/orders/{order_id}/status',
        headers={'Authorization': f"Bearer {auth_tokens['owner1']}"},
        json={'status': 'ACCEPTED'}
    )
    assert accept_res.status_code == 200
    assert accept_res.get_json()['data']['status'] == 'ACCEPTED'

    # Check stock after acceptance: 5 - 2 = 3
    with app.app_context():
        inv_after = Inventory.query.filter_by(pharmacy_id=1, medicine_id=2).first().quantity
        assert inv_after == 3


def test_prescription_rejection_flow(client, auth_tokens):
    """Test rejecting a prescription automatically rejects the order."""
    prescription_data = (io.BytesIO(b"Sample PDF Prescription"), 'rx2.pdf')
    order_res = client.post(
        '/api/orders',
        headers={'Authorization': f"Bearer {auth_tokens['customer']}"},
        data={
            'pharmacy_id': 1,
            'fulfillment_type': 'PICKUP',
            'payment_method': 'CASH',
            'items': json.dumps([{'medicine_id': 2, 'quantity': 1}]),
            'prescription': prescription_data
        },
        content_type='multipart/form-data'
    )
    order_id = order_res.get_json()['data']['id']

    # Reject prescription
    rej_res = client.patch(
        f'/api/pharmacy/orders/{order_id}/prescription',
        headers={'Authorization': f"Bearer {auth_tokens['owner1']}"},
        json={'status': 'REJECTED'}
    )
    assert rej_res.status_code == 200
    assert rej_res.get_json()['data']['order_status'] == 'REJECTED'

    # Customer checks order status
    cust_res = client.get(f'/api/orders/{order_id}', headers={'Authorization': f"Bearer {auth_tokens['customer']}"})
    assert cust_res.status_code == 200
    assert cust_res.get_json()['message'] == "Your order was not taken."


def test_insufficient_stock_acceptance_returns_409(client, auth_tokens, app):
    """Test accepting an order when stock is insufficient returns 409 and keeps order in PLACED."""
    # Create order for 5 units of Paracetamol
    order_res = client.post(
        '/api/orders',
        headers={'Authorization': f"Bearer {auth_tokens['customer']}"},
        data={
            'pharmacy_id': 1,
            'fulfillment_type': 'PICKUP',
            'payment_method': 'CASH',
            'items': json.dumps([{'medicine_id': 1, 'quantity': 5}])
        }
    )
    order_id = order_res.get_json()['data']['id']

    # Artificially lower stock to 2 in database
    with app.app_context():
        inv = Inventory.query.filter_by(pharmacy_id=1, medicine_id=1).first()
        inv.quantity = 2
        db.session.commit()

    # Owner attempts to accept order for 5 units
    accept_res = client.patch(
        f'/api/pharmacy/orders/{order_id}/status',
        headers={'Authorization': f"Bearer {auth_tokens['owner1']}"},
        json={'status': 'ACCEPTED'}
    )
    assert accept_res.status_code == 409
    assert "Requested quantity is no longer available" in accept_res.get_json()['message']

    # Verify order remains PLACED
    with app.app_context():
        order = db.session.get(Order, order_id)
        assert order.status == OrderStatus.PLACED


def test_full_order_lifecycle_and_payment_paid(client, auth_tokens):
    """Test full lifecycle for Delivery: PLACED -> ACCEPTED -> PREPARING -> OUT_FOR_DELIVERY -> COMPLETED (PAID)."""
    # 1. Place delivery order
    order_res = client.post(
        '/api/orders',
        headers={'Authorization': f"Bearer {auth_tokens['customer']}"},
        data={
            'pharmacy_id': 1,
            'fulfillment_type': 'DELIVERY',
            'delivery_address': 'Flat 202, Sector 15, Delhi',
            'payment_method': 'CASH',
            'items': json.dumps([{'medicine_id': 1, 'quantity': 1}])
        }
    )
    order_id = order_res.get_json()['data']['id']

    # 2. Accept
    res = client.patch(f'/api/pharmacy/orders/{order_id}/status', headers={'Authorization': f"Bearer {auth_tokens['owner1']}"}, json={'status': 'ACCEPTED'})
    assert res.status_code == 200

    # 3. Preparing
    res = client.patch(f'/api/pharmacy/orders/{order_id}/status', headers={'Authorization': f"Bearer {auth_tokens['owner1']}"}, json={'status': 'PREPARING'})
    assert res.status_code == 200

    # 4. Out for delivery (Disallowed: READY_FOR_PICKUP for delivery orders)
    bad_res = client.patch(f'/api/pharmacy/orders/{order_id}/status', headers={'Authorization': f"Bearer {auth_tokens['owner1']}"}, json={'status': 'READY_FOR_PICKUP'})
    assert bad_res.status_code == 400

    res = client.patch(f'/api/pharmacy/orders/{order_id}/status', headers={'Authorization': f"Bearer {auth_tokens['owner1']}"}, json={'status': 'OUT_FOR_DELIVERY'})
    assert res.status_code == 200

    # 5. Completed -> Payment status should automatically change to PAID
    res = client.patch(f'/api/pharmacy/orders/{order_id}/status', headers={'Authorization': f"Bearer {auth_tokens['owner1']}"}, json={'status': 'COMPLETED'})
    assert res.status_code == 200
    assert res.get_json()['data']['payment_status'] == PaymentStatus.PAID
    assert res.get_json()['data']['status_message'] == "Your order has been completed."


def test_inventory_management(client, auth_tokens):
    """Test owner adding and updating inventory items."""
    # List inventory
    list_res = client.get('/api/pharmacy/inventory', headers={'Authorization': f"Bearer {auth_tokens['owner2']}"})
    assert list_res.status_code == 200

    # Add existing medicine to inventory
    add_res = client.post(
        '/api/pharmacy/inventory',
        headers={'Authorization': f"Bearer {auth_tokens['owner2']}"},
        json={'medicine_id': 2, 'quantity': 12, 'price': 75.0}
    )
    assert add_res.status_code == 201
    inv_id = add_res.get_json()['data']['id']

    # Update inventory
    patch_res = client.patch(
        f'/api/pharmacy/inventory/{inv_id}',
        headers={'Authorization': f"Bearer {auth_tokens['owner2']}"},
        json={'quantity': 20, 'price': 72.0}
    )
    assert patch_res.status_code == 200
    assert patch_res.get_json()['data']['quantity'] == 20
    assert patch_res.get_json()['data']['price'] == 72.0
