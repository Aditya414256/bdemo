from .auth import auth_bp
from .medicines import medicines_bp
from .orders import orders_bp
from .pharmacy import pharmacy_bp
from .admin import admin_bp

__all__ = [
    'auth_bp',
    'medicines_bp',
    'orders_bp',
    'pharmacy_bp',
    'admin_bp'
]
