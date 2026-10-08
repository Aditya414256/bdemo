from datetime import datetime, timezone
from . import db

class PrescriptionReviewStatus:
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHOICES = [PENDING, APPROVED, REJECTED]


class Prescription(db.Model):
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)
    file_path = db.Column(db.String(255), nullable=False) # Server storage relative path
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False) # MIME or ext
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    review_status = db.Column(db.String(20), nullable=False, default=PrescriptionReviewStatus.PENDING)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], lazy=True)
    customer = db.relationship('User', foreign_keys=[customer_id], lazy=True)

    def to_dict(self):
        """Serialize prescription metadata (excluding direct server file path)."""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'customer_id': self.customer_id,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'review_status': self.review_status,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None
        }
