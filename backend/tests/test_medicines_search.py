def test_medicine_search(client):
    """Test searching medicine by name or generic name."""
    response = client.get('/api/medicines/search?q=para')
    data = response.get_json()
    assert response.status_code == 200
    assert data['success'] is True
    assert len(data['data']['medicines']) >= 1
    assert "Paracetamol" in data['data']['medicines'][0]['name']


def test_medicine_suggestions(client):
    """Test autocomplete suggestions."""
    response = client.get('/api/medicines/suggestions?q=amox')
    data = response.get_json()
    assert response.status_code == 200
    assert len(data['data']['suggestions']) >= 1
    assert data['data']['suggestions'][0]['requires_prescription'] is True


def test_pharmacy_availability_pickup(client):
    """Test medicine pharmacy availability for pickup."""
    # Search for Paracetamol (medicine_id=1)
    response = client.get('/api/medicines/1/pharmacies?method=pickup&lat=28.6139&lng=77.2090')
    data = response.get_json()
    assert response.status_code == 200
    assert data['success'] is True
    pharmacies = data['data']['pharmacies']
    assert len(pharmacies) == 2 # Both Apollo and MedPlus have Paracetamol
    # Apollo has coordinates -> distance_km should be calculated
    apollo = next(p for p in pharmacies if p['name'] == 'Apollo Test Pharmacy')
    assert apollo['distance_km'] is not None
    # MedPlus has null coordinates -> distance_km should be None
    medplus = next(p for p in pharmacies if p['name'] == 'MedPlus Test Pharmacy')
    assert medplus['distance_km'] is None


def test_pharmacy_availability_delivery_filtering(client):
    """Test pharmacy availability for delivery (MedPlus does not support delivery)."""
    response = client.get('/api/medicines/1/pharmacies?method=delivery')
    data = response.get_json()
    assert response.status_code == 200
    pharmacies = data['data']['pharmacies']
    assert len(pharmacies) == 1 # Only Apollo supports delivery
    assert pharmacies[0]['name'] == 'Apollo Test Pharmacy'


def test_pharmacy_availability_unapproved_excluded(client):
    """Ensure pending/unapproved pharmacies never appear in customer search."""
    response = client.get('/api/medicines/1/pharmacies?method=pickup')
    data = response.get_json()
    pharmacy_names = [p['name'] for p in data['data']['pharmacies']]
    assert "Pending Test Pharmacy" not in pharmacy_names
