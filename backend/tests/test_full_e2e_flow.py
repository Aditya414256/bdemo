import io
import json
import pytest
from backend.models import db, User, Pharmacy, Medicine, Inventory, Order, OrderStatus, PharmacyVerificationStatus, PrescriptionReviewStatus

def test_full_customer_to_pharmacy_and_admin_e2e(client):
    # -------------------------------------------------------------
    # 1. Customer Registration & Login
    # -------------------------------------------------------------
    reg_res = client.post('/api/auth/register/customer', json={
        'full_name': 'Aarav Gupta',
        'email': 'aarav@gmail.com',
        'phone': '9988776655',
        'password': 'password123'
    })
    assert reg_res.status_code == 201
    cust_token = reg_res.get_json()['data']['token']
    cust_headers = {'Authorization': f'Bearer {cust_token}'}

    # -------------------------------------------------------------
    # 2. Search Medicine & Availability
    # -------------------------------------------------------------
    search_res = client.get('/api/medicines/search?q=Paracetamol')
    assert search_res.status_code == 200
    meds = search_res.get_json()['data']['medicines']
    assert len(meds) > 0
    paracetamol = meds[0]

    # Availability for pickup
    avail_res = client.get(f'/api/medicines/{paracetamol["id"]}/pharmacies?method=pickup')
    assert avail_res.status_code == 200
    pharmacies = avail_res.get_json()['data']['pharmacies']
    assert len(pharmacies) > 0
    selected_pharma = pharmacies[0]
    initial_stock = selected_pharma['quantity']

    # -------------------------------------------------------------
    # 3. Customer Places Order (Store Pickup, Cash)
    # -------------------------------------------------------------
    order_data = {
        'pharmacy_id': str(selected_pharma['id']),
        'fulfillment_type': 'PICKUP',
        'payment_method': 'CASH',
        'items': json.dumps([{'medicine_id': paracetamol['id'], 'quantity': 2}])
    }
    place_res = client.post('/api/orders', data=order_data, headers=cust_headers)
    assert place_res.status_code == 201
    order_id = place_res.get_json()['data']['id']

    # VERIFY STOCK RULE: Stock is NOT reduced at PLACED
    inv = Inventory.query.filter_by(pharmacy_id=selected_pharma['id'], medicine_id=paracetamol['id']).first()
    assert inv.quantity == initial_stock, "Stock must NOT decrease when order is only PLACED"

    # Customer sees correct status and message
    cust_order_res = client.get(f'/api/orders/{order_id}', headers=cust_headers)
    assert cust_order_res.status_code == 200
    assert cust_order_res.get_json()['data']['status'] == OrderStatus.PLACED
    assert cust_order_res.get_json()['data']['status_message'] == "Your order has been placed."

    # -------------------------------------------------------------
    # 4. Pharmacy Owner Logs In & Processes Order
    # -------------------------------------------------------------
    pharma_user = db.session.get(User, selected_pharma['owner_id'])
    login_res = client.post('/api/auth/login', json={
        'email': pharma_user.email,
        'password': 'ownerpass'
    })
    assert login_res.status_code == 200
    owner_token = login_res.get_json()['data']['token']
    owner_headers = {'Authorization': f'Bearer {owner_token}'}

    # Owner views orders
    owner_orders_res = client.get('/api/pharmacy/orders', headers=owner_headers)
    assert owner_orders_res.status_code == 200
    incoming = [o for o in owner_orders_res.get_json()['data']['orders'] if o['id'] == order_id]
    assert len(incoming) == 1

    # Owner accepts order -> STOCK DEDUCTED ATOMICALLY
    accept_res = client.patch(f'/api/pharmacy/orders/{order_id}/status', json={'status': 'ACCEPTED'}, headers=owner_headers)
    assert accept_res.status_code == 200
    assert accept_res.get_json()['data']['status'] == OrderStatus.ACCEPTED

    # Verify inventory was reduced by 2
    inv_after = Inventory.query.filter_by(pharmacy_id=selected_pharma['id'], medicine_id=paracetamol['id']).first()
    assert inv_after.quantity == initial_stock - 2

    # Owner advances order: ACCEPTED -> PREPARING
    prep_res = client.patch(f'/api/pharmacy/orders/{order_id}/status', json={'status': 'PREPARING'}, headers=owner_headers)
    assert prep_res.status_code == 200
    assert prep_res.get_json()['data']['status'] == OrderStatus.PREPARING

    # Owner advances pickup order: PREPARING -> READY_FOR_PICKUP
    ready_res = client.patch(f'/api/pharmacy/orders/{order_id}/status', json={'status': 'READY_FOR_PICKUP'}, headers=owner_headers)
    assert ready_res.status_code == 200
    assert ready_res.get_json()['data']['status'] == OrderStatus.READY_FOR_PICKUP

    # Customer checks status message
    cust_check = client.get(f'/api/orders/{order_id}', headers=cust_headers)
    assert cust_check.get_json()['data']['status_message'] == "Your order is ready for pickup."

    # Owner completes order: READY_FOR_PICKUP -> COMPLETED
    comp_res = client.patch(f'/api/pharmacy/orders/{order_id}/status', json={'status': 'COMPLETED'}, headers=owner_headers)
    assert comp_res.status_code == 200
    assert comp_res.get_json()['data']['status'] == OrderStatus.COMPLETED
    assert comp_res.get_json()['data']['payment_status'] == 'PAID'

    # Customer final message
    cust_final = client.get(f'/api/orders/{order_id}', headers=cust_headers)
    assert cust_final.get_json()['data']['status_message'] == "Your order has been completed."

    # -------------------------------------------------------------
    # 5. Prescription Order Workflow
    # -------------------------------------------------------------
    rx_med = Medicine.query.filter_by(requires_prescription=True).first()
    assert rx_med is not None

    # Customer places prescription order with valid upload
    rx_data = {
        'pharmacy_id': str(selected_pharma['id']),
        'fulfillment_type': 'DELIVERY',
        'delivery_address': 'Flat 201, Green View Apartments, Delhi',
        'payment_method': 'CASH',
        'items': json.dumps([{'medicine_id': rx_med.id, 'quantity': 1}]),
        'prescription': (io.BytesIO(b'%PDF-1.4 mock prescription content'), 'rx.pdf', 'application/pdf')
    }
    rx_place_res = client.post('/api/orders', data=rx_data, headers=cust_headers)
    assert rx_place_res.status_code == 201
    rx_order_id = rx_place_res.get_json()['data']['id']

    # Owner attempts to accept without prescription approval -> Must fail
    premature_accept = client.patch(f'/api/pharmacy/orders/{rx_order_id}/status', json={'status': 'ACCEPTED'}, headers=owner_headers)
    assert premature_accept.status_code == 400
    assert "prescription" in premature_accept.get_json()['message'].lower()

    # Owner approves prescription
    rx_approve = client.patch(f'/api/pharmacy/orders/{rx_order_id}/prescription', json={'status': 'APPROVED'}, headers=owner_headers)
    assert rx_approve.status_code == 200

    # Now owner can accept
    rx_accept = client.patch(f'/api/pharmacy/orders/{rx_order_id}/status', json={'status': 'ACCEPTED'}, headers=owner_headers)
    assert rx_accept.status_code == 200
    assert rx_accept.get_json()['data']['status'] == OrderStatus.ACCEPTED

    # Delivery flow: ACCEPTED -> PREPARING -> OUT_FOR_DELIVERY -> COMPLETED
    client.patch(f'/api/pharmacy/orders/{rx_order_id}/status', json={'status': 'PREPARING'}, headers=owner_headers)
    out_res = client.patch(f'/api/pharmacy/orders/{rx_order_id}/status', json={'status': 'OUT_FOR_DELIVERY'}, headers=owner_headers)
    assert out_res.status_code == 200

    cust_out_check = client.get(f'/api/orders/{rx_order_id}', headers=cust_headers)
    assert cust_out_check.get_json()['data']['status_message'] == "Your order is out for delivery."

    # -------------------------------------------------------------
    # 6. Admin Verification Flow
    # -------------------------------------------------------------
    admin_login = client.post('/api/auth/login', json={
        'email': 'admin@test.com',
        'password': 'adminpass'
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.get_json()['data']['token']
    admin_headers = {'Authorization': f'Bearer {admin_token}'}

    pending_res = client.get('/api/admin/pharmacies/pending', headers=admin_headers)
    assert pending_res.status_code == 200
    pending_list = pending_res.get_json()['data']['pending_pharmacies']
    assert len(pending_list) > 0
    target_pending = pending_list[0]

    # Admin approves
    approve_res = client.patch(f'/api/admin/pharmacies/{target_pending["id"]}/verification', json={'status': 'APPROVED'}, headers=admin_headers)
    assert approve_res.status_code == 200
    assert approve_res.get_json()['data']['verification_status'] == PharmacyVerificationStatus.APPROVED

    # Approved pharmacy now appears in public pharmacy list
    pub_list = client.get('/api/pharmacy/list')
    assert pub_list.status_code == 200
    pub_ids = [p['id'] for p in pub_list.get_json()['data']['pharmacies']]
    assert target_pending['id'] in pub_ids
