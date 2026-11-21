"""
CampusRide — MySQL Database Setup Script
Loads all SQL files into MySQL in the correct order:
  1. schema.sql      → CREATE TABLES
  2. sample_data.sql → INSERT sample records
  3. views.sql       → CREATE VIEWS
  4. procedures.sql  → CREATE FUNCTIONS + PROCEDURES
  5. triggers.sql    → CREATE TRIGGERS

Run once:   python setup_mysql.py
"""
import subprocess
import sys
import os

MYSQL_BIN  = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
MYSQL_USER = "root"
MYSQL_PASS = "sql123"
MYSQL_HOST = "localhost"
SQL_DIR    = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sql")

SQL_FILES_IN_ORDER = [
    "schema.sql",
    "sample_data.sql",
    "views.sql",
    "procedures.sql",
    "triggers.sql",
]


def run_sql_file(filename: str):
    filepath = os.path.join(SQL_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  ⚠ SKIP: {filename} not found")
        return True

    print(f"\n  📄 Loading: {filename}")
    cmd = [
        MYSQL_BIN,
        f"-u{MYSQL_USER}",
        f"-p{MYSQL_PASS}",
        f"-h{MYSQL_HOST}",
        "--default-character-set=utf8mb4",
        "-e",
        f"SOURCE {filepath.replace(chr(92), '/')}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and "Warning" not in result.stderr:
        print(f"  ❌ ERROR in {filename}:")
        print(result.stderr[:500])
        return False
    else:
        print(f"  ✅ {filename} loaded successfully")
        if result.stdout:
            print(result.stdout[:300])
        return True


def install_pymysql():
    """Ensure pymysql is installed for SQLAlchemy MySQL support."""
    try:
        import pymysql
        print("  ✅ pymysql already installed")
    except ImportError:
        print("  📦 Installing pymysql...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pymysql", "cryptography"])
        print("  ✅ pymysql installed")


def test_connection():
    """Verify MySQL connection works with SQLAlchemy."""
    from sqlalchemy import create_engine, text
    url = f"mysql+pymysql://root:sql123@localhost:3306/campusride?charset=utf8mb4"
    try:
        eng = create_engine(url)
        with eng.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM Student")).fetchone()
            print(f"  ✅ Connection OK! Students in DB: {result[0]}")
        return True
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("  CampusRide — MySQL Setup (100% SQL-Driven Architecture)")
    print("=" * 60)

    print("\n[1/3] Installing Python MySQL driver...")
    install_pymysql()

    print("\n[2/3] Loading SQL files into MySQL 8.0...")
    for sql_file in SQL_FILES_IN_ORDER:
        success = run_sql_file(sql_file)
        if not success:
            print(f"\n❌ Setup stopped at {sql_file}. Fix the error and re-run.")
            sys.exit(1)

    print("\n[3/3] Testing SQLAlchemy connection to MySQL...")
    import importlib
    import pymysql
    if test_connection():
        print("\n" + "=" * 60)
        print("  ✅ CampusRide MySQL Setup COMPLETE!")
        print("  Database: campusride (MySQL 8.0)")
        print("  Tables:   10 tables with constraints & indexes")
        print("  Views:    6 pre-joined views")
        print("  Procs:    10 stored procedures + 7 functions")
        print("  Triggers: 7 automatic state management triggers")
        print()
        print("  Now start the server:")
        print("  > backend\\RUN_SERVER.bat")
        print("=" * 60)
    else:
        print("\n❌ Connection test failed. Check MySQL service is running.")
        sys.exit(1)
