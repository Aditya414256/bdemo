import io
import json
from backend.models import Inventory

def test_place_order_non_prescription_success(client, auth_tokens, app):
    """Test placing an order for an OTC medicine."""
    with app.app_context():
        inv_before = Inventory.query.filter_by(pharmacy_id=1, medicine_id=1).first().quantity

    response = client.post(
        '/api/orders',
        headers={'Authorization': f"Bearer {auth_tokens['customer']}"},
        data={
            'pharmacy_id': 1,
            'fulfillment_type': 'PICKUP',
            'payment_method': 'CASH',
            'customer_phone': '9876543210',
            'items': json.dumps([{'medicine_id': 1, 'quantity': 2}])
        }
    )
    data = response.get_json()
    assert response.status_code == 201
    assert data['success'] is True
    assert data['message'] == "Order placed."
    assert data['data']['status'] == "PLACED"
    assert data['data']['payment_status'] == "PENDING"
    assert data['data']['payment_method'] == "CASH"

    # CRITICAL: Stock must NOT be reduced on placement
    with app.app_context():
        inv_after = Inventory.query.filter_by(pharmacy_id=1, medicine_id=1).first().quantity
        assert inv_after == inv_before


def test_prescription_required_medicine_without_upload_fails(client, auth_tokens):
    """Test ordering prescription-required medicine without file upload fails."""
    # medicine_id=2 is Amoxicillin (requires_prescription=True)
    response = client.post(
        '/api/orders',
        headers={'Authorization': f"Bearer {auth_tokens['customer']}"},
        data={
            'pharmacy_id': 1,
            'fulfillment_type': 'PICKUP',
            'payment_method': 'CASH',
            'items': json.dumps([{'medicine_id': 2, 'quantity': 1}])
        }
    )
    data = response.get_json()
    assert response.status_code == 400
    assert data['success'] is False
    assert "prescription" in data['message'].lower()


def test_prescription_required_medicine_with_upload_success(client, auth_tokens):
    """Test ordering prescription-required medicine with valid file upload succeeds."""
    prescription_data = (io.BytesIO(b"%PDF-1.4 test prescription content"), 'rx_sample.pdf')

    response = client.post(
        '/api/orders',
        headers={'Authorization': f"Bearer {auth_tokens['customer']}"},
        data={
            'pharmacy_id': 1,
            'fulfillment_type': 'DELIVERY',
            'delivery_address': 'Flat 101, Green Apartments, Delhi',
            'payment_method': 'CASH',
            'customer_phone': '9876543210',
            'items': json.dumps([{'medicine_id': 2, 'quantity': 1}]),
            'prescription': prescription_data
        },
        content_type='multipart/form-data'
    )
    data = response.get_json()
    assert response.status_code == 201
    assert data['success'] is True
    assert data['data']['has_prescription'] is True
    assert data['data']['prescription_status'] == 'PENDING'


def test_customer_view_orders_and_status(client, auth_tokens):
    """Test customer listing orders and getting status messages."""
    # Create order first in this test
    create_res = client.post(
        '/api/orders',
        headers={'Authorization': f"Bearer {auth_tokens['customer']}"},
        data={
            'pharmacy_id': 1,
            'fulfillment_type': 'PICKUP',
            'payment_method': 'CASH',
            'customer_phone': '9876543210',
            'items': json.dumps([{'medicine_id': 1, 'quantity': 1}])
        }
    )
    assert create_res.status_code == 201
    order_id = create_res.get_json()['data']['id']

    # List all customer orders
    list_res = client.get('/api/orders', headers={'Authorization': f"Bearer {auth_tokens['customer']}"})
    assert list_res.status_code == 200
    orders = list_res.get_json()['data']['orders']
    assert len(orders) >= 1
    
    # Get individual order status
    detail_res = client.get(f'/api/orders/{order_id}', headers={'Authorization': f"Bearer {auth_tokens['customer']}"})
    assert detail_res.status_code == 200
    detail_data = detail_res.get_json()
    assert detail_data['message'] == "Your order has been placed."
