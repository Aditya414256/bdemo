def test_customer_registration(client):
    """Test customer registration and token generation."""
    response = client.post('/api/auth/register/customer', json={
        'name': 'New Customer',
        'email': 'newcustomer@test.com',
        'password': 'password123',
        'phone': '9988776655'
    })
    data = response.get_json()
    assert response.status_code == 201
    assert data['success'] is True
    assert 'token' in data['data']
    assert data['data']['user']['role'] == 'CUSTOMER'
    assert data['data']['user']['email'] == 'newcustomer@test.com'


def test_pharmacy_registration_pending(client):
    """Test pharmacy owner registration creating a PENDING pharmacy."""
    response = client.post('/api/auth/register/pharmacy', json={
        'name': 'Pharmacy Owner Bob',
        'email': 'bob@pharmacy.com',
        'password': 'password123',
        'phone': '9876500000',
        'pharmacy_name': 'Bob Chemist Store',
        'address': 'Plot 4, Market',
        'city': 'Delhi',
        'state': 'Delhi',
        'pincode': '110002',
        'supports_pickup': True,
        'supports_delivery': True
    })
    data = response.get_json()
    assert response.status_code == 201
    assert data['success'] is True
    assert data['data']['user']['role'] == 'PHARMACY_OWNER'
    assert data['data']['pharmacy']['verification_status'] == 'PENDING'


def test_login_success(client):
    """Test valid user login."""
    response = client.post('/api/auth/login', json={
        'email': 'customer@test.com',
        'password': 'custpass'
    })
    data = response.get_json()
    assert response.status_code == 200
    assert data['success'] is True
    assert 'token' in data['data']
    assert data['data']['user']['email'] == 'customer@test.com'


def test_login_invalid_password(client):
    """Test login failure with bad credentials."""
    response = client.post('/api/auth/login', json={
        'email': 'customer@test.com',
        'password': 'wrongpassword'
    })
    data = response.get_json()
    assert response.status_code == 401
    assert data['success'] is False


def test_get_me_endpoint(client, auth_tokens):
    """Test GET /api/auth/me with Bearer token."""
    response = client.get('/api/auth/me', headers={
        'Authorization': f"Bearer {auth_tokens['customer']}"
    })
    data = response.get_json()
    assert response.status_code == 200
    assert data['data']['user']['email'] == 'customer@test.com'


def test_unauthorized_without_token(client):
    """Test access denied when token is missing."""
    response = client.get('/api/auth/me')
    assert response.status_code == 401
