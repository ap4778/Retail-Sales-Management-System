# Retail Sales Management System
### 21CSC205P – Database Management Systems Mini Project

**Students:** Yash Vardhan Singh (RA2411003011056) | Aditya Pratap (RA2411003011064)  
**Guide:** Dr. M. Karthikeyan, Associate Professor  
**Department:** Computing Technologies, SRM Institute of Science and Technology

---

## Project Structure

```
retail_sales_project/
├── frontend/
│   └── index.html          ← Complete Single-Page Web Application
├── backend/
│   ├── app.py              ← Flask REST API Backend (MySQL)
│   ├── db_connect.py       ← Python MySQL Connectivity Layer
│   ├── retailshop.db       ← Legacy SQLite file (no longer used)
│   ├── schema.sql          ← SQL Schema + Sample Data
│   └── requirements.txt    ← Python dependencies
├── test_endpoints.py       ← API endpoint verification script
├── TODO.md                 ← Implementation tracker
└── README.md
```

---

## How to Run

### Step 1 – Install Python Dependencies

```bash
pip install -r backend/requirements.txt
```

Dependencies: `flask`, `flask-cors`, `mysql-connector-python`

### Step 2 - Configure and Start MySQL

Ensure a local or remote MySQL server is running.

The backend reads these optional environment variables:
- `MYSQL_HOST` (default: `localhost`)
- `MYSQL_PORT` (default: `3306`)
- `MYSQL_USER` (default: `root`)
- `MYSQL_PASSWORD` (default: empty)
- `MYSQL_DATABASE` (default: `retailshop_manage`)

On startup, the backend automatically creates the configured database and required tables (if your MySQL user has permissions).

### Step 3 – Start the Flask Backend

```bash
python backend/app.py
```

The API will start at: **http://localhost:5000**

You should see:
```
==================================================
🚀 Starting Retail Sales Management API...
📍 API available at: http://localhost:5000
==================================================
```

### Step 4 – Open the Frontend

Open `frontend/index.html` in any modern web browser (Chrome, Firefox, Edge).  
No server required — it runs entirely in the browser and connects to `http://localhost:5000/api`.

### Step 5 – Verify Endpoints (Optional)

Run the automated test script to verify all API endpoints:

```bash
python test_endpoints.py
```

Expected output:
```
============================================================
 Retail Sales API Endpoint Verification
============================================================
[PASS] Health Check - GET /api/health - Status 200
[PASS] Get All Customers - GET /api/customers - Status 200
[PASS] Add Customer - POST /api/customers - Status 201
...
============================================================
 Results: 16 passed, 0 failed
============================================================
```

---

## Database Schema

| Table    | Primary Key    | Foreign Keys                     |
|----------|---------------|----------------------------------|
| Customer | customer_id   | —                                |
| Product  | product_id    | —                                |
| Sales    | transaction_id | customer_id → Customer, product_id → Product |

---

## API Endpoints

| Method | Endpoint                        | Description                          |
|--------|---------------------------------|--------------------------------------|
| GET    | `/api/health`                   | Health check                         |
| GET    | `/api/customers`                | List all customers                   |
| POST   | `/api/customers`                | Add a new customer                   |
| GET    | `/api/customers/<id>`           | Get customer by ID                   |
| GET    | `/api/products`                 | List all products                    |
| POST   | `/api/products`                 | Add a new product                    |
| GET    | `/api/products/<id>`            | Get product by ID                    |
| GET    | `/api/sales`                    | List all sales                       |
| POST   | `/api/sales`                    | Record a new sale                    |
| GET    | `/api/sales/<id>`               | Get sale by transaction ID           |
| GET    | `/api/dashboard/stats`          | Dashboard statistics                 |
| GET    | `/api/dashboard/recent-sales`   | Recent 5 sales                       |
| GET    | `/api/reports/sales`            | Filtered sales report                |
| GET    | `/api/reports/category-summary` | Category-wise revenue summary        |
| GET    | `/api/calculate-total`          | Auto-calculate sale total            |

---

## Features

### Frontend (index.html)
- **Dashboard** – Live counts of customers, products, transactions, total revenue
- **Customers** – Add new customers; search and list all customers with transaction count
- **Products** – Add new products with auto profit margin calculation
- **Sales** – Record sales with auto-calculated total; search by Transaction/Customer ID
- **Reports** – Filter by customer, product, date range; category-wise revenue breakdown

### Backend (app.py + db_connect.py)
- Full REST API with CORS enabled
- MySQL database (configured via environment variables)
- All CRUD operations for Customer, Product, and Sales
- Dashboard and reporting endpoints with JOINs and aggregations
- Auto-calculate total endpoint for sales form

---

## Technology Stack

| Layer       | Technology                     |
|-------------|--------------------------------|
| Frontend    | HTML5, CSS3, JavaScript (ES6+) |
| Backend     | Python 3.x + Flask             |
| DB Driver   | mysql-connector-python         |
| Database    | MySQL                          |

---

## Notes

- MySQL schema/tables are auto-created by `backend/db_connect.py` during backend startup (no sample data is inserted).
- `backend/retailshop.db` is a legacy SQLite file and is not used by the current backend.
- The backend uses Flask's built-in development server. For production, use a WSGI server like Gunicorn.
- CORS is enabled to allow the frontend (opened via `file://` or `http://`) to communicate with the API.

