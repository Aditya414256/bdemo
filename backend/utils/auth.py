from functools import wraps
from datetime import datetime, timezone, timedelta
import jwt
from flask import request, current_app, g
from ..models import db
from ..models.user import User
from .responses import api_response

def generate_token(user_id: int, role: str, email: str) -> str:
    """Generate a JWT token for the authenticated user."""
    expiration_hours = current_app.config.get('JWT_EXPIRATION_HOURS', 24)
    secret_key = current_app.config.get('JWT_SECRET_KEY', current_app.config['SECRET_KEY'])
    
    payload = {
        'user_id': user_id,
        'role': role,
        'email': email,
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(hours=expiration_hours)
    }
    return jwt.encode(payload, secret_key, algorithm='HS256')


def decode_token(token: str):
    """Decode and validate a JWT token string."""
    secret_key = current_app.config.get('JWT_SECRET_KEY', current_app.config['SECRET_KEY'])
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_token_from_header() -> str:
    """Extract Bearer token from the Authorization header."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == 'bearer':
        return parts[1]
    return None


def jwt_required(f):
    """Decorator to require a valid Bearer JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        if not token:
            return api_response(False, "Authorization token is missing. Please provide a Bearer token.", status_code=401)
        
        payload = decode_token(token)
        if not payload:
            return api_response(False, "Invalid or expired token. Please log in again.", status_code=401)
        
        user = db.session.get(User, payload['user_id'])
        if not user:
            return api_response(False, "User account not found.", status_code=401)
        
        # Store in flask g context
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def roles_required(*allowed_roles):
    """Decorator to restrict access to specific roles (e.g. CUSTOMER, PHARMACY_OWNER, ADMIN)."""
    def decorator(f):
        @wraps(f)
        @jwt_required
        def decorated(*args, **kwargs):
            user = g.current_user
            if user.role not in allowed_roles:
                return api_response(
                    False, 
                    f"Access forbidden. This action requires one of the following roles: {', '.join(allowed_roles)}.",
                    status_code=403
                )
            return f(*args, **kwargs)
        return decorated
    return decorator


def get_current_user() -> User:
    """Helper to retrieve the current user from Flask's g context."""
    return getattr(g, 'current_user', None)
