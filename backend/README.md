# MediFind – Pharmacy & Medicine Availability Backend

MediFind is a RESTful backend API built with **Python**, **Flask**, and **SQLite (Flask-SQLAlchemy)**. It enables customers to search for medicines, check real-time stock availability across nearby pharmacies, upload prescriptions when required, and place pickup or cash-on-delivery orders. It empowers pharmacy owners to manage inventory, review prescription attachments, and handle the order preparation lifecycle with strict multi-tenant authorization and atomic stock deduction.

---

## 1. Project Directory Structure

```text
backend/
├── app.py                     # Flask application factory, CORS, blueprints & error handlers
├── config.py                  # Environment configuration (Dev, Test, Prod)
├── requirements.txt           # Python dependencies
├── .env.example               # Example environment configuration
├── seed.py                    # Database seeding script with realistic demo data
│
├── models/                    # SQLAlchemy Database Models
│   ├── __init__.py            # DB instance and model exports
│   ├── user.py                # Users table (CUSTOMER, PHARMACY_OWNER, ADMIN)
│   ├── pharmacy.py            # Pharmacies table (verification status, pickup/delivery flags)
│   ├── medicine.py            # Medicines catalog (OTC vs Prescription-Required)
│   ├── inventory.py           # Pharmacy Inventory & stock tracking
│   ├── order.py               # Orders, OrderItems, and OrderStatusHistory
│   └── prescription.py        # Uploaded prescriptions & review metadata
│
├── routes/                    # API Route Blueprints
│   ├── __init__.py            # Route blueprint bundle
│   ├── auth.py                # Registration, Login, Logout, /me
│   ├── medicines.py           # Search, Autocomplete suggestions, Pharmacy availability
│   ├── orders.py              # Order placement (multipart/json), Customer orders list/detail
│   ├── pharmacy.py            # Owner order management, prescription review, inventory CRUD
│   └── admin.py               # Admin pharmacy verification (approve/reject)
│
├── services/                  # Business Logic Layer
│   ├── __init__.py
│   ├── order_service.py       # Atomic stock deduction & state transition enforcement
│   └── distance_service.py    # Haversine distance calculation & fallback ranker
│
├── utils/                     # Helpers & Security
│   ├── __init__.py
│   ├── auth.py                # JWT token generation, verification, and role decorators
│   ├── file_upload.py         # Secure file validation, UUID naming, and safe storage
│   └── responses.py           # Standardized JSON response format wrapper
│
├── uploads/                   # Secure storage for uploaded prescriptions
│   └── prescriptions/
│
├── tests/                     # Pytest automated test suite
│   ├── conftest.py            # Test fixtures and in-memory test database
│   ├── test_auth.py
│   ├── test_medicines_search.py
│   ├── test_orders_and_prescriptions.py
│   ├── test_pharmacy_and_stock.py
│   └── test_admin.py
│
└── README.md                  # Complete documentation and viva guide
```

---

## 2. Quick Setup & Run Instructions

### Step 1: Navigate to Project Directory
Open your terminal in the project root:
```bash
cd "c:/Users/Admin/OneDrive/Desktop/My PROJECT"
```

### Step 2: (Optional) Create and Activate Virtual Environment
```bash
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Windows Command Prompt (cmd):
.\venv\Scripts\activate.bat
```

### Step 3: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env` if you wish to customize port or secret keys:
```bash
copy backend\.env.example backend\.env
```

### Step 5: Seed the Database
Initialize tables and populate realistic demo accounts, pharmacies, medicines, and inventory:
```bash
python backend/seed.py
```

### Step 6: Run the Backend Server
```bash
python -m backend.app
```
The server will start on: **`http://127.0.0.1:5000`**

### Step 7: Run Automated Tests
```bash
python -m pytest backend/tests/ -v
```

---

## 3. Demo User Accounts

| Role | Name | Email | Password | Details / Assigned Pharmacy |
| :--- | :--- | :--- | :--- | :--- |
| **ADMIN** | System Admin | `admin@medifind.com` | `admin123` | System Administrator |
| **PHARMACY OWNER** | Rajesh Sharma | `apollo@pharmacy.com` | `pharmacy123` | Apollo Pharmacy (Approved, Pickup & Delivery) |
| **PHARMACY OWNER** | Dr. Sunita Patel | `wellness@pharmacy.com` | `pharmacy123` | Wellness Forever (Approved, Pickup Only) |
| **PHARMACY OWNER** | Vikram Verma | `medplus@pharmacy.com` | `pharmacy123` | MedPlus Health (Approved, Delivery Only) |
| **PENDING OWNER** | Anil Kumar | `citymed@pharmacy.com` | `pharmacy123` | CityMed (Awaiting Admin Verification) |
| **CUSTOMER** | Rahul Sharma | `rahul@gmail.com` | `customer123` | Demo Customer 1 |
| **CUSTOMER** | Priya Nair | `priya@gmail.com` | `customer123` | Demo Customer 2 |

---

## 4. API Endpoints Reference

All API responses follow a consistent JSON envelope:
```json
{
  "success": true,
  "message": "Human readable message",
  "data": { ... }
}
```

### Authentication (`/api/auth`)
| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register/customer` | Public | Register new customer (`name`, `email`, `password`, `phone`) |
| `POST` | `/api/auth/register/pharmacy` | Public | Register pharmacy owner + pharmacy (creates `PENDING` status) |
| `POST` | `/api/auth/login` | Public | Login with `email` and `password`, returns Bearer JWT token |
| `POST` | `/api/auth/logout` | Token | Logout endpoint |
| `GET` | `/api/auth/me` | Token | Get authenticated user profile & pharmacy (if owner) |

### Medicines & Availability (`/api/medicines`)
| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/medicines/search?q=crocin` | Public | Search catalog by name, brand, generic, strength, category |
| `GET` | `/api/medicines/suggestions?q=amox` | Public | Autocomplete query suggestions |
| `GET` | `/api/medicines/<id>/pharmacies?method=pickup` | Public | List approved pharmacies with stock > 0 supporting pickup |
| `GET` | `/api/medicines/<id>/pharmacies?method=delivery` | Public | List approved pharmacies with stock > 0 supporting delivery |

*Query parameters supported:* `method` (`pickup`/`delivery`), `lat`, `lng`, `city`, `pincode`.

### Customer Orders (`/api/orders`)
| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/orders` | Customer | Place order (`multipart/form-data`). Validates pharmacy, stock, and prescription. Stock is **NOT** deducted here. |
| `GET` | `/api/orders` | Customer | Retrieve list of logged-in customer's orders |
| `GET` | `/api/orders/<id>` | Customer | Retrieve real-time status and customer-facing message for an order |

### Pharmacy Owner (`/api/pharmacy`)
| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/pharmacy/orders` | Pharmacy Owner | List all orders received by the owner's pharmacy |
| `GET` | `/api/pharmacy/orders/<id>` | Pharmacy Owner | Get full order & customer details for owner's pharmacy |
| `PATCH` | `/api/pharmacy/orders/<id>/status` | Pharmacy Owner | Update order status (`ACCEPTED`, `PREPARING`, `READY_FOR_PICKUP`, `OUT_FOR_DELIVERY`, `COMPLETED`, `REJECTED`). Atomic stock deduction occurs on `ACCEPTED`. |
| `GET` | `/api/pharmacy/orders/<id>/prescription` | Pharmacy Owner | Securely download/view prescription file |
| `PATCH` | `/api/pharmacy/orders/<id>/prescription` | Pharmacy Owner | Review prescription (`APPROVED` or `REJECTED`). Rejecting prescription rejects the order automatically. |
| `GET` | `/api/pharmacy/inventory` | Pharmacy Owner | List owner's pharmacy inventory |
| `POST` | `/api/pharmacy/inventory` | Pharmacy Owner | Add existing medicine from catalog to inventory (`medicine_id`, `quantity`, `price`) |
| `PATCH` | `/api/pharmacy/inventory/<id>` | Pharmacy Owner | Update stock quantity or price |

### Admin Verification (`/api/admin`)
| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/admin/pharmacies/pending` | Admin | List all pharmacies pending verification |
| `PATCH` | `/api/admin/pharmacies/<id>/verification` | Admin | Set verification status (`APPROVED` or `REJECTED`) |

---

## 5. Core Business Logic & Architecture

### 1. Order Status Transition Matrix
Orders move forward through a strictly controlled state machine based on fulfillment type:

```text
                      [ PLACED ]
                          │
          ┌───────────────┴───────────────┐
          │                               │
    (Stock Available &                    │ (Owner Rejects or
     Rx Approved)                         │  Rx Rejected)
          ↓                               ↓
     [ ACCEPTED ]                   [ REJECTED ] (Terminal)
          │                         "Your order was not taken."
          ↓
    [ PREPARING ]
          │
   ┌──────┴──────────────────────────────────────┐
   │ (If Fulfillment = PICKUP)                   │ (If Fulfillment = DELIVERY)
   ↓                                             ↓
[ READY_FOR_PICKUP ]                     [ OUT_FOR_DELIVERY ]
"Your order is ready for pickup."       "Your order is out for delivery."
   │                                             │
   └──────────────────────┬──────────────────────┘
                          ↓
                    [ COMPLETED ] (Terminal)
              "Your order has been completed."
              (Sets payment_status = PAID)
```

### 2. Exact Stock Handling Rule
- **At Order Placement (`status = PLACED`):** Stock is **never** deducted or reserved. The inventory quantity remains unchanged.
- **At Order Acceptance (`status = ACCEPTED`):**
  1. The backend verifies whether a prescription was required and ensures its status is `APPROVED`.
  2. The latest inventory is queried within an atomic database transaction.
  3. If current stock $\ge$ requested quantity, the quantity is decremented atomically.
  4. If stock is insufficient, the transaction rolls back, HTTP `409 Conflict` is returned (`"Requested quantity is no longer available."`), and the order stays `PLACED`.

### 3. Prescription Storage Security
- Prescriptions are uploaded via `multipart/form-data`.
- Files are assigned random, unique UUID filenames and stored in `uploads/prescriptions/`.
- Prescriptions are **never exposed as static public URLs**.
- Access is restricted through authenticated endpoints (`/api/pharmacy/orders/<id>/prescription`), ensuring only the pharmacy owner assigned to the order can view the file.

### 4. Multi-Tenant Pharmacy Isolation
- Pharmacy owners cannot supply an arbitrary `pharmacy_id`.
- The backend automatically resolves the owner's pharmacy from their JWT token (`g.current_user.id`).
- Any attempt to view or mutate another pharmacy's orders, prescriptions, or inventory returns `404 Not Found` or `403 Forbidden`.

### 5. Distance & Location Fallback
- If both customer and pharmacy coordinates are available, great-circle distance is calculated using the **Haversine formula**.
- If coordinates are unavailable, `distance_km` is returned as `null`, and the system deterministically sorts results by:
  1. Exact Pincode match
  2. City match
  3. Lowest Price
  4. Pharmacy ID

---

## 6. Frontend Integration with JavaScript `fetch`

Because the frontend runs on a separate development server (e.g., Live Server on port 5500), requests are authenticated using Bearer tokens.

### Storing & Attaching JWT Token
```javascript
// 1. Save token on Login
localStorage.setItem('medifind_token', responseData.data.token);

// 2. Fetch authenticated data
const token = localStorage.getItem('medifind_token');
const res = await fetch('http://127.0.0.1:5000/api/orders', {
    method: 'GET',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});
const data = await res.json();
```

### Polling for Real-Time Status Updates
```javascript
// Poll order status every 3 seconds
function pollOrderStatus(orderId) {
    const token = localStorage.getItem('medifind_token');
    const interval = setInterval(async () => {
        const response = await fetch(`http://127.0.0.1:5000/api/orders/${orderId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const result = await response.json();
        
        if (result.success) {
            console.log("Current Status:", result.data.status);
            console.log("Message:", result.message);
            
            // Stop polling once order is in a terminal state
            if (['COMPLETED', 'REJECTED'].includes(result.data.status)) {
                clearInterval(interval);
            }
        }
    }, 3000);
}
```

---

## 7. College Viva Guide (Questions & Simple Explanations)

### Q1: What is the database design and why SQLite?
**Answer:** SQLite is a serverless, file-based relational database that requires no external server setup, making the project lightweight and easily portable across evaluation machines. The schema consists of 7 interconnected tables:
1. `users`: Stores credentials (hashed with Werkzeug) and user roles (`CUSTOMER`, `PHARMACY_OWNER`, `ADMIN`).
2. `pharmacies`: Stores store name, address, verification status (`PENDING`, `APPROVED`), and pickup/delivery options.
3. `medicines`: Central medicine master catalog with name, strength, dosage form, and prescription requirement flag.
4. `inventory`: Many-to-many relationship linking pharmacies and medicines with current quantity and unit price.
5. `orders`: Order header tracking customer, pharmacy, status, fulfillment method, and payment status.
6. `order_items`: Line items storing medicine ID, quantity, and unit price.
7. `prescriptions`: Tracks uploaded doctor prescriptions, original filename, and review status (`PENDING`, `APPROVED`, `REJECTED`).
8. `order_status_history`: Audit trail recording every status change, timestamp, and actor.

### Q2: Why is stock NOT deducted when the customer places an order?
**Answer:** In realistic on-demand pharmacy workflows, an order placement is simply a request. If stock was deducted at placement, a customer could hoard inventory without pharmacy confirmation, or an invalid prescription might lock up medicines. Therefore, stock is deducted **only when the pharmacy owner verifies the prescription and clicks Accept**, inside an atomic transaction.

### Q3: How do you prevent race conditions during stock acceptance?
**Answer:** In `services/order_service.py`, order acceptance is wrapped in a database transaction. The system queries the inventory for `quantity >= requested_quantity`, decrements the quantity, updates the status to `ACCEPTED`, and commits. If another order accepted the remaining stock in between, the check fails, the transaction rolls back, and HTTP `409 Conflict` is returned.

### Q4: How is authentication and multi-tenancy handled?
**Answer:** We use stateless **JSON Web Tokens (JWT)**. When a user logs in, the server signs a token containing `user_id` and `role`. On subsequent requests, the `@jwt_required` and `@roles_required` decorators verify the signature and attach the user to Flask's `g` context. Pharmacy owners can only access data where `pharmacy.owner_id == g.current_user.id`.

### Q5: How are prescriptions protected from public access?
**Answer:** Uploaded files are stored in a non-public folder (`backend/uploads/prescriptions/`) with random UUID filenames. They cannot be accessed via static URL paths like `/static/file.jpg`. Instead, a secure endpoint checks the pharmacy owner's credentials before streaming the file via `send_file()`.
