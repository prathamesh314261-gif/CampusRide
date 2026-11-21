"""
CampusRide — Complete Data Seeder
Inserts missing Insurance, Reviews, Dispute records into MySQL.
Verifies all tables have data for DBMS demonstration.
Run: python seed_all.py
"""
import sys
sys.path.insert(0, '.')
from database import engine
from sqlalchemy import text

def seed():
    with engine.connect() as conn:
        print("🌱 Seeding CampusRide database...")

        # ── Insurance records ──────────────────────────────────────
        insurance = [
            (1, 'HDFC ERGO',           'HDG-2026-001', 500000, '2026-01-01', '2027-01-01'),
            (2, 'New India Assurance',  'NIA-2026-002', 300000, '2026-01-01', '2027-01-01'),
            (3, 'Bajaj Allianz',        'BAJ-2026-003', 400000, '2026-01-01', '2027-01-01'),
            (4, 'ICICI Lombard',        'ICL-2026-004', 250000, '2026-01-01', '2027-01-01'),
            (5, 'SBI General',          'SBI-2025-005', 350000, '2025-01-01', '2025-12-31'),  # EXPIRED
            (6, 'HDFC ERGO',            'HDG-2026-006', 500000, '2026-03-01', '2027-03-01'),
            (7, 'Oriental Insurance',   'ORI-2026-007', 300000, '2026-06-01', '2027-06-01'),
            (8, 'United India',         'UII-2026-008', 200000, '2026-01-01', '2027-01-01'),
            (9, 'New India Assurance',  'NIA-2026-009', 600000, '2026-01-01', '2027-01-01'),
        ]
        for vid, prov, pol, cov, vf, vt in insurance:
            try:
                conn.execute(text("""
                    INSERT IGNORE INTO Insurance
                        (vehicle_id, provider, policy_number, coverage_amount, valid_from, valid_to)
                    VALUES (:vid, :prov, :pol, :cov, :vf, :vt)
                """), dict(vid=vid, prov=prov, pol=pol, cov=cov, vf=vf, vt=vt))
            except Exception as e:
                print(f"  ⚠ Insurance skip: {e}")

        # ── Reviews ────────────────────────────────────────────────
        reviews = [
            (2, 2, 1, 5, 'Excellent Honda Activa — very smooth ride!'),
            (3, 3, 2, 4, 'Good TVS Jupiter, clean and well maintained.'),
            (4, 4, 6, 5, 'Loved the Yamaha FZ-S. Will book again!'),
        ]
        for rid, rev, vid, rat, com in reviews:
            try:
                conn.execute(text("""
                    INSERT IGNORE INTO Review (rental_id, reviewer_id, vehicle_id, rating, comment)
                    VALUES (:rid, :rev, :vid, :rat, :com)
                """), dict(rid=rid, rev=rev, vid=vid, rat=rat, com=com))
            except Exception as e:
                print(f"  ⚠ Review skip: {e}")

        # ── Disputes ───────────────────────────────────────────────
        try:
            conn.execute(text("""
                INSERT IGNORE INTO Dispute (rental_id, raised_by, reason, status)
                VALUES (1, 1, 'Vehicle had scratches not disclosed before rental', 'Open')
            """))
        except Exception as e:
            print(f"  ⚠ Dispute skip: {e}")

        # ── Update vehicle avg_rating from reviews ─────────────────
        try:
            conn.execute(text("""
                UPDATE Vehicle v SET
                    avg_rating   = (SELECT ROUND(AVG(rating), 1) FROM Review r WHERE r.vehicle_id = v.vehicle_id),
                    total_reviews= (SELECT COUNT(*) FROM Review r WHERE r.vehicle_id = v.vehicle_id)
                WHERE vehicle_id IN (SELECT DISTINCT vehicle_id FROM Review)
            """))
        except Exception as e:
            print(f"  ⚠ Rating update skip: {e}")

        conn.commit()
        print("✅ Seeding complete!\n")

        # ── Verify counts ──────────────────────────────────────────
        tables = ['Student','Vehicle','Rental','Payment','Insurance','Review','Dispute','Coupon','AuditLog','Maintenance']
        print("📊 Table row counts:")
        for t in tables:
            try:
                n = conn.execute(text(f"SELECT COUNT(*) FROM `{t}`")).scalar()
                status = "✅" if n > 0 else "⚠️ EMPTY"
                print(f"  {status}  {t:<20} {n} rows")
            except Exception as e:
                print(f"  ❌  {t:<20} ERROR: {e}")

        print()
        print("🔍 Available vehicles (vw_available_vehicles):")
        rows = conn.execute(text("SELECT vehicle_id, brand, model, hourly_rate FROM vw_available_vehicles")).fetchall()
        for r in rows:
            print(f"  #{r[0]:>2}  {r[1]} {r[2]:<20}  ₹{r[3]}/hr")

        print()
        print("🛡️  Insurance status (vw_insurance_status):")
        rows = conn.execute(text("SELECT license_plate, provider, insurance_status, days_remaining FROM vw_insurance_status")).fetchall()
        for r in rows:
            icon = "✅" if r[2] == 'Active' else "❌"
            print(f"  {icon}  {r[0]:<15}  {r[1]:<25}  {r[2]}  ({r[3]} days)")

        print()
        print("🎟️  Active coupons:")
        rows = conn.execute(text("SELECT code, discount_percentage FROM Coupon WHERE is_active=1 AND CURDATE() BETWEEN valid_from AND valid_to")).fetchall()
        for r in rows:
            print(f"  {r[0]:<12}  {r[1]}% off")

        print()
        print("=" * 50)
        print("🏍️  CampusRide is ready for demonstration!")
        print("   Start server: cd backend && python -m uvicorn main:app --reload")
        print("   API Docs:     http://localhost:8000/docs")
        print("=" * 50)

if __name__ == "__main__":
    seed()
