from flask import Blueprint, request
from ..models import db, UserRole, Pharmacy, PharmacyVerificationStatus
from ..utils.auth import roles_required
from ..utils.responses import api_response

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/pharmacies/pending', methods=['GET'])
@roles_required(UserRole.ADMIN)
def get_pending_pharmacies():
    """List all pharmacies awaiting admin verification."""
    pending_list = Pharmacy.query.filter_by(
        verification_status=PharmacyVerificationStatus.PENDING
    ).order_by(Pharmacy.created_at.asc()).all()

    return api_response(
        True,
        f"Found {len(pending_list)} pending pharmacy verification requests.",
        data={'pending_pharmacies': [p.to_dict(include_owner=True) for p in pending_list]},
        status_code=200
    )


@admin_bp.route('/pharmacies/<int:pharmacy_id>/verification', methods=['PATCH'])
@roles_required(UserRole.ADMIN)
def update_pharmacy_verification(pharmacy_id: int):
    """
    Approve or reject a pharmacy verification request.
    Body: { "status": "APPROVED" | "REJECTED" }
    """
    pharmacy = db.session.get(Pharmacy, pharmacy_id)
    if not pharmacy:
        return api_response(False, "Pharmacy not found.", status_code=404)

    data = request.get_json() or {}
    new_status = data.get('status', '').strip().upper()

    if new_status not in [PharmacyVerificationStatus.APPROVED, PharmacyVerificationStatus.REJECTED]:
        return api_response(
            False,
            f"Invalid status. Must be one of: {PharmacyVerificationStatus.APPROVED}, {PharmacyVerificationStatus.REJECTED}.",
            status_code=400
        )

    pharmacy.verification_status = new_status
    db.session.commit()

    return api_response(
        True,
        f"Pharmacy '{pharmacy.name}' verification status set to {new_status}.",
        data=pharmacy.to_dict(include_owner=True),
        status_code=200
    )
