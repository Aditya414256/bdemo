"""
MediFind Database Seeder Script.
Seeds realistic demo data: Admin, Pharmacy Owners, Pharmacies, Customers, Medicines, and Inventory.
"""

from pathlib import Path
import sys

# Ensure backend directory is in python path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from backend.app import create_app
from backend.models import (
    db, User, UserRole, Pharmacy, PharmacyVerificationStatus,
    Medicine, Inventory
)

def seed_database():
    app = create_app()

    with app.app_context():
        print("[*] Clearing existing database tables...")
        db.drop_all()
        db.create_all()
        print("[+] Tables initialized successfully.")

        # --- 1. Seed Users ---
        print("[*] Seeding Users (Admin, Pharmacy Owners, Customers)...")
        
        # 1 Admin
        admin = User(
            name="System Admin",
            email="admin@medifind.com",
            phone="9876543210",
            role=UserRole.ADMIN
        )
        admin.set_password("admin123")
        db.session.add(admin)

        # 3 Pharmacy Owners
        owner1 = User(
            name="Rajesh Sharma",
            email="apollo@pharmacy.com",
            phone="9811122233",
            role=UserRole.PHARMACY_OWNER
        )
        owner1.set_password("pharmacy123")
        db.session.add(owner1)

        owner2 = User(
            name="Dr. Sunita Patel",
            email="wellness@pharmacy.com",
            phone="9822233344",
            role=UserRole.PHARMACY_OWNER
        )
        owner2.set_password("pharmacy123")
        db.session.add(owner2)

        owner3 = User(
            name="Vikram Verma",
            email="medplus@pharmacy.com",
            phone="9833344455",
            role=UserRole.PHARMACY_OWNER
        )
        owner3.set_password("pharmacy123")
        db.session.add(owner3)

        # 1 Pending Verification Owner
        owner_pending = User(
            name="Anil Kumar",
            email="citymed@pharmacy.com",
            phone="9844455566",
            role=UserRole.PHARMACY_OWNER
        )
        owner_pending.set_password("pharmacy123")
        db.session.add(owner_pending)

        # 2 Customers
        customer1 = User(
            name="Rahul Sharma",
            email="rahul@gmail.com",
            phone="9899001122",
            role=UserRole.CUSTOMER
        )
        customer1.set_password("customer123")
        db.session.add(customer1)

        customer2 = User(
            name="Priya Nair",
            email="priya@gmail.com",
            phone="9899112233",
            role=UserRole.CUSTOMER
        )
        customer2.set_password("customer123")
        db.session.add(customer2)

        db.session.flush()

        # --- 2. Seed Pharmacies ---
        print("[*] Seeding Pharmacies...")

        # Pharmacy 1: Apollo Pharmacy (Approved, Pickup & Delivery, with Coordinates)
        pharmacy1 = Pharmacy(
            owner_id=owner1.id,
            name="Apollo Pharmacy - Connaught Place",
            phone="011-23415678",
            email="apollo.cp@gmail.com",
            address="Block M, Inner Circle, Connaught Place",
            city="New Delhi",
            state="Delhi",
            pincode="110001",
            latitude=28.6328,
            longitude=77.2197,
            verification_status=PharmacyVerificationStatus.APPROVED,
            supports_pickup=True,
            supports_delivery=True,
            is_active=True
        )
        db.session.add(pharmacy1)

        # Pharmacy 2: Wellness Forever (Approved, Pickup Only, with Coordinates)
        pharmacy2 = Pharmacy(
            owner_id=owner2.id,
            name="Wellness Forever Chemist",
            phone="011-26598741",
            address="Shop 4, Hauz Khas Main Market",
            city="New Delhi",
            state="Delhi",
            pincode="110016",
            latitude=28.5494,
            longitude=77.2001,
            verification_status=PharmacyVerificationStatus.APPROVED,
            supports_pickup=True,
            supports_delivery=False,
            is_active=True
        )
        db.session.add(pharmacy2)

        # Pharmacy 3: MedPlus Health (Approved, Delivery Only, Coordinates NULL to test fallback)
        pharmacy3 = Pharmacy(
            owner_id=owner3.id,
            name="MedPlus Healthcare Store",
            phone="011-27489632",
            address="C-12, Sector 18, Commercial Belt",
            city="Noida",
            state="Uttar Pradesh",
            pincode="201301",
            latitude=None, # Testing null coordinate fallback
            longitude=None,
            verification_status=PharmacyVerificationStatus.APPROVED,
            supports_pickup=True,
            supports_delivery=True,
            is_active=True
        )
        db.session.add(pharmacy3)

        # Pharmacy 4: CityMed Pharmacy (Pending Admin Verification)
        pharmacy4 = Pharmacy(
            owner_id=owner_pending.id,
            name="CityMed 24x7 Chemist",
            phone="011-29874561",
            address="Plot 15, Dwarka Sector 10",
            city="New Delhi",
            state="Delhi",
            pincode="110075",
            latitude=28.5815,
            longitude=77.0601,
            verification_status=PharmacyVerificationStatus.PENDING,
            supports_pickup=True,
            supports_delivery=True,
            is_active=True
        )
        db.session.add(pharmacy4)

        db.session.flush()

        # --- 3. Seed Medicines ---
        print("[*] Seeding Medicines...")
        medicines = [
            # OTC / Non-Prescription
            Medicine(
                name="Paracetamol 500mg (Crocin Advance)",
                generic_name="Paracetamol",
                brand_name="Crocin",
                strength="500mg",
                dosage_form="Tablet",
                category="Analgesic & Antipyretic",
                requires_prescription=False,
                description="Fast pain relief and fever reducing tablet. Commonly used for headache, toothache, body ache and mild fever."
            ),
            Medicine(
                name="Ibuprofen 400mg (Brufen)",
                generic_name="Ibuprofen",
                brand_name="Brufen",
                strength="400mg",
                dosage_form="Tablet",
                category="NSAID / Pain Relief",
                requires_prescription=False,
                description="Non-steroidal anti-inflammatory drug used for relieving pain, reducing inflammation and lowering fever."
            ),
            Medicine(
                name="Cetirizine 10mg (Cetzine)",
                generic_name="Cetirizine Hydrochloride",
                brand_name="Cetzine",
                strength="10mg",
                dosage_form="Tablet",
                category="Antihistamine / Allergy",
                requires_prescription=False,
                description="Provides relief from allergy symptoms like runny nose, sneezing, itchy or watery eyes, and hives."
            ),
            Medicine(
                name="Benadryl Cough Formula Syrup",
                generic_name="Diphenhydramine HCl",
                brand_name="Benadryl",
                strength="100ml",
                dosage_form="Syrup",
                category="Cough & Cold",
                requires_prescription=False,
                description="Soothes irritating throat coughs and provides quick relief from chest congestion."
            ),
            # Prescription Required Medicines
            Medicine(
                name="Amoxicillin 500mg (Novamox 500)",
                generic_name="Amoxicillin Trihydrate",
                brand_name="Novamox",
                strength="500mg",
                dosage_form="Capsule",
                category="Antibiotic",
                requires_prescription=True,
                description="Broad-spectrum penicillin antibiotic used to treat bacterial infections of ear, nose, throat, skin, and urinary tract."
            ),
            Medicine(
                name="Azithromycin 500mg (Azee 500)",
                generic_name="Azithromycin",
                brand_name="Azee",
                strength="500mg",
                dosage_form="Tablet",
                category="Antibiotic",
                requires_prescription=True,
                description="Macrolide antibiotic used for respiratory tract infections, pneumonia, and tonsillitis. Strict doctor prescription required."
            ),
            Medicine(
                name="Metformin 500mg (Glycomet 500)",
                generic_name="Metformin Hydrochloride",
                brand_name="Glycomet",
                strength="500mg",
                dosage_form="Tablet",
                category="Anti-Diabetic",
                requires_prescription=True,
                description="Prescription medication used with diet and exercise to lower blood sugar in patients with type 2 diabetes."
            )
        ]

        for med in medicines:
            db.session.add(med)

        db.session.flush()

        # --- 4. Seed Inventory ---
        print("[*] Seeding Inventory across Pharmacies...")
        # Med indices:
        # 0: Paracetamol (No Rx)
        # 1: Ibuprofen (No Rx)
        # 2: Cetirizine (No Rx)
        # 3: Benadryl (No Rx)
        # 4: Amoxicillin (Rx required)
        # 5: Azithromycin (Rx required)
        # 6: Metformin (Rx required)

        inventory_records = [
            # Pharmacy 1 (Apollo): Has Paracetamol, Ibuprofen, Amoxicillin, Azithromycin
            Inventory(pharmacy_id=pharmacy1.id, medicine_id=medicines[0].id, quantity=50, price=30.0, stock_status='IN_STOCK'),
            Inventory(pharmacy_id=pharmacy1.id, medicine_id=medicines[1].id, quantity=25, price=45.0, stock_status='IN_STOCK'),
            Inventory(pharmacy_id=pharmacy1.id, medicine_id=medicines[4].id, quantity=15, price=115.0, stock_status='IN_STOCK'),
            Inventory(pharmacy_id=pharmacy1.id, medicine_id=medicines[5].id, quantity=20, price=140.0, stock_status='IN_STOCK'),
            
            # Pharmacy 2 (Wellness Forever): Has Paracetamol, Cetirizine, Benadryl, Amoxicillin (Low stock: 2)
            Inventory(pharmacy_id=pharmacy2.id, medicine_id=medicines[0].id, quantity=40, price=32.0, stock_status='IN_STOCK'),
            Inventory(pharmacy_id=pharmacy2.id, medicine_id=medicines[2].id, quantity=60, price=22.0, stock_status='IN_STOCK'),
            Inventory(pharmacy_id=pharmacy2.id, medicine_id=medicines[3].id, quantity=18, price=110.0, stock_status='IN_STOCK'),
            Inventory(pharmacy_id=pharmacy2.id, medicine_id=medicines[4].id, quantity=2, price=120.0, stock_status='IN_STOCK'), # Low stock for test

            # Pharmacy 3 (MedPlus): Has Ibuprofen, Cetirizine, Metformin (Intentionally lacks Paracetamol)
            Inventory(pharmacy_id=pharmacy3.id, medicine_id=medicines[1].id, quantity=30, price=42.0, stock_status='IN_STOCK'),
            Inventory(pharmacy_id=pharmacy3.id, medicine_id=medicines[2].id, quantity=45, price=20.0, stock_status='IN_STOCK'),
            Inventory(pharmacy_id=pharmacy3.id, medicine_id=medicines[6].id, quantity=35, price=65.0, stock_status='IN_STOCK'),
        ]

        for inv in inventory_records:
            db.session.add(inv)

        db.session.commit()

        print("\n========================================================")
        print("  MediFind Database Seeded Successfully! ")
        print("========================================================")
        print("Demo User Credentials:")
        print("  - Admin:            admin@medifind.com     / admin123")
        print("  - Pharmacy Owner 1: apollo@pharmacy.com    / pharmacy123 (Apollo Pharmacy - Approved)")
        print("  - Pharmacy Owner 2: wellness@pharmacy.com  / pharmacy123 (Wellness Forever - Approved)")
        print("  - Pharmacy Owner 3: medplus@pharmacy.com   / pharmacy123 (MedPlus - Approved, Fallback Coordinates)")
        print("  - Pending Owner:    citymed@pharmacy.com   / pharmacy123 (CityMed - PENDING Verification)")
        print("  - Customer 1:       rahul@gmail.com        / customer123")
        print("  - Customer 2:       priya@gmail.com        / customer123")
        print("========================================================\n")

if __name__ == '__main__':
    seed_database()
