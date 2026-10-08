from datetime import datetime, timezone
from . import db

class Inventory(db.Model):
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id', ondelete='CASCADE'), nullable=False, index=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id', ondelete='CASCADE'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Float, nullable=False)
    stock_status = db.Column(db.String(20), nullable=False, default='IN_STOCK') # 'IN_STOCK' or 'OUT_OF_STOCK'
    last_updated_at = db.Column(
        db.DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.UniqueConstraint('pharmacy_id', 'medicine_id', name='uq_pharmacy_medicine'),
        db.CheckConstraint('quantity >= 0', name='check_inventory_quantity_non_negative'),
        db.CheckConstraint('price >= 0', name='check_inventory_price_non_negative')
    )

    def sync_stock_status(self):
        """Update stock_status string based on current quantity."""
        self.stock_status = 'IN_STOCK' if self.quantity > 0 else 'OUT_OF_STOCK'

    def to_dict(self, include_medicine=True, include_pharmacy=False):
        """Serialize inventory item to dictionary."""
        data = {
            'id': self.id,
            'pharmacy_id': self.pharmacy_id,
            'medicine_id': self.medicine_id,
            'quantity': self.quantity,
            'price': self.price,
            'stock_status': self.stock_status,
            'last_updated_at': self.last_updated_at.isoformat() if self.last_updated_at else None
        }
        if include_medicine and self.medicine:
            data['medicine'] = self.medicine.to_dict()
        if include_pharmacy and self.pharmacy:
            data['pharmacy'] = self.pharmacy.to_dict()
        return data
