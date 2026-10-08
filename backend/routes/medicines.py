from flask import Blueprint, request
from sqlalchemy import or_
from ..models import db, Medicine, Pharmacy, Inventory, PharmacyVerificationStatus
from ..services.distance_service import rank_pharmacies
from ..utils.responses import api_response

medicines_bp = Blueprint('medicines', __name__, url_prefix='/api/medicines')

@medicines_bp.route('/search', methods=['GET'])
def search_medicines():
    """
    Search medicines by query across name, generic_name, brand_name, strength, and dosage_form.
    Query param: ?q=paracetamol
    """
    query_str = request.args.get('q', '').strip()
    if not query_str:
        return api_response(True, "Please enter a search query.", data={'medicines': []}, status_code=200)

    search_pattern = f"%{query_str}%"
    medicines = Medicine.query.filter(
        or_(
            Medicine.name.ilike(search_pattern),
            Medicine.generic_name.ilike(search_pattern),
            Medicine.brand_name.ilike(search_pattern),
            Medicine.strength.ilike(search_pattern),
            Medicine.dosage_form.ilike(search_pattern),
            Medicine.category.ilike(search_pattern)
        )
    ).all()

    return api_response(
        True,
        f"Found {len(medicines)} medicines matching '{query_str}'.",
        data={'medicines': [m.to_dict() for m in medicines]},
        status_code=200
    )


@medicines_bp.route('/suggestions', methods=['GET'])
def get_suggestions():
    """
    Autocomplete suggestions for medicine search bar.
    Query param: ?q=para
    """
    query_str = request.args.get('q', '').strip()
    if not query_str:
        return api_response(True, "Empty query.", data={'suggestions': []}, status_code=200)

    search_pattern = f"%{query_str}%"
    medicines = Medicine.query.filter(
        or_(
            Medicine.name.ilike(search_pattern),
            Medicine.brand_name.ilike(search_pattern),
            Medicine.generic_name.ilike(search_pattern)
        )
    ).limit(10).all()

    suggestions = [
        {
            'id': m.id,
            'name': m.name,
            'generic_name': m.generic_name,
            'strength': m.strength,
            'dosage_form': m.dosage_form,
            'requires_prescription': m.requires_prescription
        }
        for m in medicines
    ]

    return api_response(True, "Suggestions retrieved.", data={'suggestions': suggestions}, status_code=200)


@medicines_bp.route('/<int:medicine_id>/pharmacies', methods=['GET'])
def get_pharmacies_for_medicine(medicine_id: int):
    """
    Fetch available pharmacies holding stock for a specific medicine.
    Query params:
      - method: 'pickup' or 'delivery' (default: pickup)
      - lat: customer latitude (optional)
      - lng: customer longitude (optional)
      - city: customer city for fallback sorting (optional)
      - pincode: customer pincode for fallback sorting (optional)
    """
    medicine = db.session.get(Medicine, medicine_id)
    if not medicine:
        return api_response(False, "Medicine not found.", status_code=404)

    method = request.args.get('method', 'pickup').strip().lower()
    customer_lat = request.args.get('lat', type=float)
    customer_lng = request.args.get('lng', type=float)
    customer_city = request.args.get('city', '').strip()
    customer_pincode = request.args.get('pincode', '').strip()

    # Query active, approved pharmacies with quantity > 0
    query = db.session.query(Pharmacy, Inventory).join(
        Inventory, Pharmacy.id == Inventory.pharmacy_id
    ).filter(
        Inventory.medicine_id == medicine_id,
        Inventory.quantity > 0,
        Pharmacy.is_active == True,
        Pharmacy.verification_status == PharmacyVerificationStatus.APPROVED
    )

    if method == 'delivery':
        query = query.filter(Pharmacy.supports_delivery == True)
    else:
        query = query.filter(Pharmacy.supports_pickup == True)

    pharmacies_with_inv = query.all()

    ranked_results = rank_pharmacies(
        pharmacies_with_inv,
        customer_lat=customer_lat,
        customer_lon=customer_lng,
        customer_city=customer_city,
        customer_pincode=customer_pincode
    )

    return api_response(
        True,
        f"Found {len(ranked_results)} available pharmacies.",
        data={
            'medicine': medicine.to_dict(),
            'fulfillment_method': method,
            'pharmacies': ranked_results
        },
        status_code=200
    )
