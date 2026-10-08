import io
import pytest
from pathlib import Path
import sys

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app import create_app
from backend.config import TestingConfig
from backend.models import (
    db, User, UserRole, Pharmacy, PharmacyVerificationStatus,
    Medicine, Inventory
)
from backend.utils.auth import generate_token

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        
        # Seed test data
        admin = User(name="Test Admin", email="admin@test.com", role=UserRole.ADMIN)
        admin.set_password("adminpass")
        db.session.add(admin)

        owner1 = User(name="Apollo Owner", email="owner1@test.com", role=UserRole.PHARMACY_OWNER)
        owner1.set_password("ownerpass")
        db.session.add(owner1)

        owner2 = User(name="MedPlus Owner", email="owner2@test.com", role=UserRole.PHARMACY_OWNER)
        owner2.set_password("ownerpass")
        db.session.add(owner2)

        customer = User(name="Rahul Customer", email="customer@test.com", phone="9876543210", role=UserRole.CUSTOMER)
        customer.set_password("custpass")
        db.session.add(customer)

        db.session.flush()

        # Pharmacies
        pharmacy1 = Pharmacy(
            owner_id=owner1.id,
            name="Apollo Test Pharmacy",
            phone="011-111111",
            address="123 Main St",
            city="Delhi",
            state="Delhi",
            pincode="110001",
            latitude=28.6139,
            longitude=77.2090,
            verification_status=PharmacyVerificationStatus.APPROVED,
            supports_pickup=True,
            supports_delivery=True,
            is_active=True
        )
        db.session.add(pharmacy1)

        pharmacy2 = Pharmacy(
            owner_id=owner2.id,
            name="MedPlus Test Pharmacy",
            phone="011-222222",
            address="456 Cross Rd",
            city="Noida",
            state="UP",
            pincode="201301",
            latitude=None,
            longitude=None,
            verification_status=PharmacyVerificationStatus.APPROVED,
            supports_pickup=True,
            supports_delivery=False,
            is_active=True
        )
        db.session.add(pharmacy2)

        # Pending Pharmacy
        pending_owner = User(name="Pending Owner", email="pending@test.com", role=UserRole.PHARMACY_OWNER)
        pending_owner.set_password("ownerpass")
        db.session.add(pending_owner)
        db.session.flush()

        pending_pharmacy = Pharmacy(
            owner_id=pending_owner.id,
            name="Pending Test Pharmacy",
            address="789 Lane",
            city="Gurgaon",
            state="Haryana",
            pincode="122001",
            verification_status=PharmacyVerificationStatus.PENDING,
            supports_pickup=True,
            supports_delivery=True,
            is_active=True
        )
        db.session.add(pending_pharmacy)

        # Medicines
        med_otc = Medicine(
            name="Paracetamol 500mg",
            generic_name="Paracetamol",
            brand_name="Crocin",
            strength="500mg",
            dosage_form="Tablet",
            category="Pain Relief",
            requires_prescription=False
        )
        db.session.add(med_otc)

        med_rx = Medicine(
            name="Amoxicillin 500mg",
            generic_name="Amoxicillin",
            brand_name="Novamox",
            strength="500mg",
            dosage_form="Capsule",
            category="Antibiotic",
            requires_prescription=True
        )
        db.session.add(med_rx)

        db.session.flush()

        # Inventories
        # Apollo has both OTC (qty=10) and Rx (qty=5)
        inv1 = Inventory(pharmacy_id=pharmacy1.id, medicine_id=med_otc.id, quantity=10, price=25.0, stock_status='IN_STOCK')
        inv2 = Inventory(pharmacy_id=pharmacy1.id, medicine_id=med_rx.id, quantity=5, price=80.0, stock_status='IN_STOCK')
        db.session.add_all([inv1, inv2])

        # MedPlus only has OTC (qty=8)
        inv3 = Inventory(pharmacy_id=pharmacy2.id, medicine_id=med_otc.id, quantity=8, price=26.0, stock_status='IN_STOCK')
        db.session.add(inv3)

        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_tokens(app):
    with app.app_context():
        admin = User.query.filter_by(email="admin@test.com").first()
        owner1 = User.query.filter_by(email="owner1@test.com").first()
        owner2 = User.query.filter_by(email="owner2@test.com").first()
        customer = User.query.filter_by(email="customer@test.com").first()

        return {
            'admin': generate_token(admin.id, admin.role, admin.email),
            'owner1': generate_token(owner1.id, owner1.role, owner1.email),
            'owner2': generate_token(owner2.id, owner2.role, owner2.email),
            'customer': generate_token(customer.id, customer.role, customer.email),
            'customer_user': customer,
            'owner1_user': owner1
        }
