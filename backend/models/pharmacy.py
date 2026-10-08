from datetime import datetime, timezone
from . import db

class PharmacyVerificationStatus:
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    
    CHOICES = [PENDING, APPROVED, REJECTED]


class Pharmacy(db.Model):
    __tablename__ = 'pharmacies'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    license_number = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(20), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    verification_status = db.Column(db.String(20), nullable=False, default=PharmacyVerificationStatus.PENDING)
    supports_pickup = db.Column(db.Boolean, nullable=False, default=True)
    supports_delivery = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    inventory_items = db.relationship('Inventory', backref='pharmacy', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='pharmacy', lazy=True)

    def to_dict(self, include_owner=False):
        """Serialize pharmacy to dictionary."""
        data = {
            'id': self.id,
            'owner_id': self.owner_id,
            'name': self.name,
            'license_number': self.license_number,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'pincode': self.pincode,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'verification_status': self.verification_status,
            'supports_pickup': self.supports_pickup,
            'supports_delivery': self.supports_delivery,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_owner and self.owner:
            data['owner'] = self.owner.to_dict()
        return data
