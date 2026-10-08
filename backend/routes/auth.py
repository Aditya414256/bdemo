from flask import Blueprint, request
from ..models import db, User, UserRole, Pharmacy, PharmacyVerificationStatus
from ..utils.auth import generate_token, jwt_required, get_current_user
from ..utils.responses import api_response

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register/customer', methods=['POST'])
def register_customer():
    """Register a new customer account."""
    data = request.get_json() or {}
    
    name = (data.get('name') or data.get('full_name') or '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    phone = data.get('phone', '').strip()

    if not name:
        return api_response(False, "Name is required.", status_code=400)
    if not email or '@' not in email:
        return api_response(False, "A valid email address is required.", status_code=400)
    if not password or len(password) < 6:
        return api_response(False, "Password must be at least 6 characters long.", status_code=400)

    if User.query.filter_by(email=email).first():
        return api_response(False, "An account with this email already exists.", status_code=409)

    user = User(
        name=name,
        email=email,
        phone=phone if phone else None,
        role=UserRole.CUSTOMER
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    token = generate_token(user.id, user.role, user.email)
    return api_response(
        True,
        "Customer account registered successfully.",
        data={
            'token': token,
            'user': user.to_dict()
        },
        status_code=201
    )


@auth_bp.route('/register/pharmacy', methods=['POST'])
def register_pharmacy():
    """
    Register a pharmacy owner along with their pharmacy details.
    Initial verification_status is set to PENDING.
    """
    data = request.get_json() or {}

    owner_name = (data.get('name') or data.get('full_name') or '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    phone = data.get('phone', '').strip()

    pharmacy_name = data.get('pharmacy_name', '').strip()
    license_number = data.get('license_number', '').strip()
    address = data.get('address', '').strip()
    city = data.get('city', '').strip()
    state = data.get('state', '').strip()
    pincode = data.get('pincode', '').strip()
    pharmacy_phone = (data.get('pharmacy_phone') or phone).strip()
    pharmacy_email = (data.get('pharmacy_email') or email).strip().lower()

    # Optional fields
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    supports_pickup = bool(data.get('supports_pickup', True))
    supports_delivery = bool(data.get('supports_delivery', False))

    if not owner_name:
        return api_response(False, "Owner name is required.", status_code=400)
    if not email or '@' not in email:
        return api_response(False, "Valid email address is required.", status_code=400)
    if not password or len(password) < 6:
        return api_response(False, "Password must be at least 6 characters long.", status_code=400)
    if not pharmacy_name:
        return api_response(False, "Pharmacy name is required.", status_code=400)
    if not address or not city or not state or not pincode:
        return api_response(False, "Complete pharmacy address (address, city, state, pincode) is required.", status_code=400)

    if User.query.filter_by(email=email).first():
        return api_response(False, "An account with this email already exists.", status_code=409)

    # 1. Create User as PHARMACY_OWNER
    user = User(
        name=owner_name,
        email=email,
        phone=phone if phone else None,
        role=UserRole.PHARMACY_OWNER
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush() # Obtain user.id

    # 2. Create Pharmacy (Pending verification)
    pharmacy = Pharmacy(
        owner_id=user.id,
        name=pharmacy_name,
        license_number=license_number if license_number else None,
        phone=pharmacy_phone if pharmacy_phone else None,
        email=pharmacy_email if pharmacy_email else None,
        address=address,
        city=city,
        state=state,
        pincode=pincode,
        latitude=float(latitude) if latitude is not None and str(latitude).strip() != '' else None,
        longitude=float(longitude) if longitude is not None and str(longitude).strip() != '' else None,
        verification_status=PharmacyVerificationStatus.PENDING,
        supports_pickup=supports_pickup,
        supports_delivery=supports_delivery,
        is_active=True
    )
    db.session.add(pharmacy)
    db.session.commit()

    token = generate_token(user.id, user.role, user.email)
    return api_response(
        True,
        "Pharmacy registration submitted. Account is pending verification by admin.",
        data={
            'token': token,
            'user': user.to_dict(),
            'pharmacy': pharmacy.to_dict()
        },
        status_code=201
    )


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user with email and password."""
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return api_response(False, "Email and password are required.", status_code=400)

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return api_response(False, "Invalid email or password.", status_code=401)

    token = generate_token(user.id, user.role, user.email)

    response_data = {
        'token': token,
        'user': user.to_dict()
    }

    # If pharmacy owner, attach pharmacy profile
    if user.role == UserRole.PHARMACY_OWNER:
        pharmacy = Pharmacy.query.filter_by(owner_id=user.id).first()
        response_data['pharmacy'] = pharmacy.to_dict() if pharmacy else None

    return api_response(True, "Login successful.", data=response_data, status_code=200)


@auth_bp.route('/logout', methods=['POST'])
@jwt_required
def logout():
    """Client-side token disposal endpoint."""
    return api_response(True, "Logged out successfully.", status_code=200)


@auth_bp.route('/me', methods=['GET'])
@jwt_required
def get_me():
    """Fetch current authenticated user profile."""
    user = get_current_user()
    data = {
        'user': user.to_dict()
    }
    if user.role == UserRole.PHARMACY_OWNER:
        pharmacy = Pharmacy.query.filter_by(owner_id=user.id).first()
        data['pharmacy'] = pharmacy.to_dict() if pharmacy else None

    return api_response(True, "User profile retrieved.", data=data, status_code=200)
