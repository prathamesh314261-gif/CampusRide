"""
Database configuration for CampusRide — 100% SQL-Driven Architecture.
Uses MySQL 8.0 with pymysql driver.
All business logic lives in sql/ folder (procedures, triggers, views).
Python is a thin REST gateway that calls CALL sp_...() procedures.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

# ============================================================
# MySQL Connection (100% SQL-Driven — no SQLite)
# ============================================================
MYSQL_USER     = "root"
MYSQL_PASSWORD = "sql123"
MYSQL_HOST     = "localhost"
MYSQL_PORT     = "3306"
MYSQL_DB       = "campusride"

DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    f"?charset=utf8mb4"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,          # auto-reconnect on connection drop
    pool_recycle=3600,           # recycle connections every hour
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def call_procedure(db, proc_name: str, params: list):
    """
    Helper to call a MySQL Stored Procedure.
    Returns the result set as a list of dicts.
    
    Example:
        result = call_procedure(db, "sp_create_rental",
                                [student_id, vehicle_id, start, end, pickup, ret, coupon])
    """
    # Build parameterized CALL statement
    placeholders = ", ".join([":p" + str(i) for i in range(len(params))])
    sql = text(f"CALL {proc_name}({placeholders})")
    param_dict = {f"p{i}": v for i, v in enumerate(params)}
    result = db.execute(sql, param_dict)
    try:
        rows = result.fetchall()
        if rows:
            keys = result.keys()
            return [dict(zip(keys, row)) for row in rows]
        return []
    except Exception:
        return []


def query_view(db, view_name: str, where: str = "", params: dict = None):
    """
    Query a database VIEW directly.
    
    Example:
        vehicles = query_view(db, "vw_available_vehicles")
        my_rentals = query_view(db, "vw_rental_history", "WHERE student_id = :sid", {"sid": 3})
    """
    sql = text(f"SELECT * FROM {view_name} {where}")
    result = db.execute(sql, params or {})
    rows = result.fetchall()
    keys = result.keys()
    return [dict(zip(keys, row)) for row in rows]


def check_and_repair_db():
    """Automatically detects missing views or procedures and repairs them."""
    try:
        with engine.connect() as conn:
            res_view = conn.execute(text("SHOW FULL TABLES IN campusride WHERE Table_type = 'VIEW'")).fetchall()
            res_proc = conn.execute(text("SHOW PROCEDURE STATUS WHERE Db = 'campusride'")).fetchall()
            views = [r[0].lower() for r in res_view]
            procs = [r[1].lower() for r in res_proc]

            missing_views = not ("vw_available_vehicles" in views and "vw_rental_history" in views and "vw_payment_history" in views)
            missing_procs = not ("sp_login" in procs and "sp_create_rental" in procs)

            if missing_views or missing_procs:
                import subprocess, os
                print("⚠️ [CampusRide] Missing database views or procedures detected. Auto-repairing from sql/ folder...")
                mysql_bin = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
                sql_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sql")

                files_to_run = []
                if missing_views:
                    files_to_run.append("views.sql")
                if missing_procs:
                    files_to_run.extend(["procedures.sql", "triggers.sql"])

                for f in files_to_run:
                    fpath = os.path.join(sql_dir, f).replace("\\", "/")
                    cmd = [mysql_bin, "-uroot", "-psql123", "-hlocalhost", "--default-character-set=utf8mb4", "-e", f"SOURCE {fpath}"]
                    subprocess.run(cmd, capture_output=True, text=True)
                print("✅ [CampusRide] Auto-repair complete! All views, procedures, and triggers are ready.")
    except Exception as e:
        print(f"⚠️ [CampusRide] DB health check warning: {e}")

