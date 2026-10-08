def test_admin_list_pending_pharmacies(client, auth_tokens):
    """Test admin fetching list of pending pharmacies."""
    response = client.get('/api/admin/pharmacies/pending', headers={'Authorization': f"Bearer {auth_tokens['admin']}"})
    data = response.get_json()
    assert response.status_code == 200
    assert data['success'] is True
    assert len(data['data']['pharmacies']) >= 1
    assert data['data']['pharmacies'][0]['name'] == "Pending Test Pharmacy"


def test_admin_approve_pharmacy(client, auth_tokens):
    """Test admin approving a pending pharmacy."""
    response = client.patch(
        '/api/admin/pharmacies/3/verification',
        headers={'Authorization': f"Bearer {auth_tokens['admin']}"},
        json={'status': 'APPROVED'}
    )
    data = response.get_json()
    assert response.status_code == 200
    assert data['success'] is True
    assert data['data']['pharmacy']['verification_status'] == 'APPROVED'


def test_non_admin_forbidden(client, auth_tokens):
    """Ensure non-admin accounts cannot access admin routes."""
    response = client.get(
        '/api/admin/pharmacies/pending',
        headers={'Authorization': f"Bearer {auth_tokens['customer']}"}
    )
    assert response.status_code == 403
