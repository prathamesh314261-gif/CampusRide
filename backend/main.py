"""
CampusRide FastAPI Application — 100% SQL-Driven Architecture.

Architecture:
  ┌─────────────────┐
  │  Frontend HTML  │  ← Static pages (login, dashboard, booking)
  └────────┬────────┘
           │ HTTP REST
  ┌────────▼────────┐
  │  FastAPI (Python│  ← Thin gateway only (auth tokens + routing)
  │  routes/*.py)   │
  └────────┬────────┘
           │ CALL sp_...() / SELECT * FROM vw_...
  ┌────────▼────────────────────────────────────┐
  │             MySQL 8.0 Database               │
  │  Tables: 10  │  Views: 6  │  Triggers: 7    │
  │  Functions: 7│  Procedures: 10               │
  │  All business logic lives here (sql/ folder) │
  └──────────────────────────────────────────────┘

To set up the database:
  python backend/setup_mysql.py
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ No ORM model import — MySQL schema is managed entirely by sql/schema.sql
# Tables are NOT auto-created by SQLAlchemy; they exist in MySQL via setup_mysql.py

app = FastAPI(
    title="CampusRide API",
    version="3.0.0",
    description="100% SQL-Driven Campus Vehicle Rental System"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    from database import check_and_repair_db
    check_and_repair_db()


@app.get("/")
def root():
    return {
        "status":  "ok",
        "message": "CampusRide API v3.0 — 100% SQL-Driven",
        "version": "3.0.0",
        "architecture": {
            "database":   "MySQL 8.0",
            "procedures": 10,
            "functions":  7,
            "triggers":   7,
            "views":      6
        }
    }


# ============================================================
# Register all route modules
# ============================================================
from routes.auth        import router as auth_router
from routes.vehicles    import router as vehicles_router
from routes.rentals     import router as rentals_router
from routes.payments    import router as payments_router
from routes.maintenance import router as maintenance_router
from routes.admin       import router as admin_router
from routes.coupons     import router as coupons_router
from routes.insurance   import router as insurance_router

from routes.security    import router as security_router

app.include_router(auth_router)
app.include_router(vehicles_router)
app.include_router(rentals_router)
app.include_router(payments_router)
app.include_router(maintenance_router)
app.include_router(admin_router)
app.include_router(coupons_router)
app.include_router(insurance_router)
app.include_router(security_router)

from routes.reviews    import router as reviews_router

app.include_router(reviews_router)

try:
    from routes.ml import router as ml_router
    app.include_router(ml_router)
except Exception:
    pass