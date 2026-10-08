from datetime import datetime, timezone
from . import db

class Medicine(db.Model):
    __tablename__ = 'medicines'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    generic_name = db.Column(db.String(200), nullable=True, index=True)
    brand_name = db.Column(db.String(200), nullable=True, index=True)
    strength = db.Column(db.String(50), nullable=True) # e.g. 500mg, 10ml
    dosage_form = db.Column(db.String(50), nullable=True) # Tablet, Capsule, Syrup, Injection, Ointment
    category = db.Column(db.String(100), nullable=True) # Pain Relief, Antibiotics, Antipyretic, etc.
    requires_prescription = db.Column(db.Boolean, nullable=False, default=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    inventories = db.relationship('Inventory', backref='medicine', lazy=True, cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='medicine', lazy=True)

    def to_dict(self):
        """Serialize medicine to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'generic_name': self.generic_name,
            'brand_name': self.brand_name,
            'strength': self.strength,
            'dosage_form': self.dosage_form,
            'category': self.category,
            'requires_prescription': self.requires_prescription,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
