# CampusRide — Pure DBMS Backend Project

A campus vehicle rental platform built on a **100% DBMS-driven architecture**.
All business logic lives inside MySQL — Python (FastAPI) is only a thin REST gateway.

## Architecture

```
Frontend HTML Pages
        |  HTTP REST
FastAPI (Python) — thin gateway only (JWT auth + routing)
        |  CALL sp_...() / SELECT * FROM vw_...
MySQL 8.0 Database
  - 10 Tables
  - 7 SQL Functions
  - 10 Stored Procedures
  - 7 Triggers
  - 6 Views
  - Full Transaction Support
```

## DBMS Operations Covered

| Operation | SQL File | Description |
|-----------|----------|-------------|
| INSERT | queries.sql (A) | Register, Add Vehicle, Book, Pay, Review |
| SELECT | queries.sql (B) | Browse Vehicles, History, Reports |
| UPDATE | queries.sql (C) | Profile, Status, Ratings |
| DELETE | queries.sql (D) | Cleanup, Archive |
| JOIN | queries.sql (E) | Multi-table rental reports |
| Subqueries | queries.sql (F) | Analytics, Filtering |
| Views | views.sql | 6 pre-built reporting views |
| Stored Procedures | procedures.sql | 10 procedures for all operations |
| Triggers | triggers.sql | 7 triggers for auto-updates |
| Transactions | queries.sql (K) | Atomic booking, payment, rollback |

## Database Tables

| Table | Purpose |
|-------|---------|
| Student | Users (students, owners, admins) |
| Vehicle | Rental vehicles |
| Coupon | Discount coupons |
| Rental | Booking records |
| Payment | Payment records |
| Review | Vehicle reviews |
| Maintenance | Service records |
| Insurance | Vehicle insurance |
| Dispute | Customer complaints |
| AuditLog | Security & activity log |

## Setup

### 1. Install Dependencies
```
pip install -r requirements.txt
```

### 2. Setup MySQL Database
```
python backend/setup_mysql.py
```
(Uses MySQL root/sql123 by default — edit backend/database.py to change)

### 3. Seed Sample Data
```
python backend/seed_all.py
```

### 4. Run Server
```
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 15501 --reload
```
Or double-click: `backend/RUN_SERVER.bat`

### 5. Open Frontend
Open in browser: `http://127.0.0.1:15501/CampusRide/frontend/index.html`

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Student | rohit@vit.edu | password123 |
| Owner | amit@vit.edu | owner123 |
| Admin | admin@vit.edu | admin123 |

## API Endpoints

| Module | Base URL |
|--------|----------|
| Auth | /api/auth |
| Vehicles | /api/vehicles |
| Rentals | /api/rentals |
| Payments | /api/payments |
| Coupons | /api/coupons |
| Maintenance | /api/maintenance |
| Insurance | /api/insurance |
| Reviews | /api/reviews |
| Admin | /api/admin |
| AI/ML | /api/ml |

## AI/ML Features

- **Vehicle Recommendation** — Cosine similarity on student preferences
- **Demand Prediction** — Time-series forecasting by hour/day
- **Payment Anomaly Detection** — Z-score + Isolation Forest
- **Predictive Maintenance** — Vehicle health scoring
- **Dynamic Pricing** — Demand-supply based suggestions
