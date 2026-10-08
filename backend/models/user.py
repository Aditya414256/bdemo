from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class UserRole:
    CUSTOMER = "CUSTOMER"
    PHARMACY_OWNER = "PHARMACY_OWNER"
    ADMIN = "ADMIN"
    
    CHOICES = [CUSTOMER, PHARMACY_OWNER, ADMIN]


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), nullable=False, default=UserRole.CUSTOMER)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    pharmacies = db.relationship('Pharmacy', backref='owner', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='customer', lazy=True, foreign_keys='Order.customer_id')

    def set_password(self, password: str):
        """Hash and set user password securely."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify plain password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Convert user model to public serializable dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'full_name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
