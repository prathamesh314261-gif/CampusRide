"""
Admin routes — 100% SQL-Driven.
All queries use raw SQL (SELECT from tables/views) or CALL stored procedures.
Zero ORM model imports.
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
import auth

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(token: str, db: Session):
    """Verify admin role using raw SQL — no ORM."""
    payload = auth.verify_token(token)
    uid = int(payload.get("sub"))
    row = db.execute(
        text("SELECT role FROM Student WHERE student_id = :id"), {"id": uid}
    ).fetchone()
    if not row or row._mapping["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return uid


@router.get("/stats")
def get_stats(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dashboard stats — all computed by MySQL aggregation queries.
    ✅ Zero Python arithmetic — GROUP BY, COUNT, SUM inside SQL.
    """
    require_admin(token, db)

    row = db.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM Student)                                              AS total_students,
            (SELECT COUNT(*) FROM Vehicle)                                              AS total_vehicles,
            (SELECT COUNT(*) FROM Rental)                                               AS total_rentals,
            (SELECT COUNT(*) FROM Rental WHERE status = 'Active')                       AS active_rentals,
            (SELECT COUNT(*) FROM Rental WHERE status = 'Completed')                    AS completed_rentals,
            (SELECT COALESCE(SUM(amount),0) FROM Payment WHERE payment_status='Completed') AS total_revenue,
            (SELECT COUNT(*) FROM Vehicle WHERE availability_status = 'Available')      AS available_vehicles,
            (SELECT COUNT(*) FROM Dispute  WHERE status = 'Open')                       AS open_disputes,
            (SELECT COUNT(*) FROM AuditLog WHERE DATE(timestamp) = CURDATE())           AS events_today
    """)).fetchone()

    m = row._mapping
    return {
        "total_students":    int(m["total_students"]),
        "total_vehicles":    int(m["total_vehicles"]),
        "total_rentals":     int(m["total_rentals"]),
        "active_rentals":    int(m["active_rentals"]),
        "completed_rentals": int(m["completed_rentals"]),
        "total_revenue":     float(m["total_revenue"]),
        "available_vehicles":int(m["available_vehicles"]),
        "open_disputes":     int(m["open_disputes"]),
        "events_today":      int(m["events_today"])
    }


@router.get("/students")
def get_all_students(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """List all students — direct SQL SELECT."""
    require_admin(token, db)
    rows = db.execute(text("""
        SELECT student_id, full_name, email, phone, department, hostel,
               role, roll_number, account_status, trust_score,
               failed_attempts, created_at
        FROM Student ORDER BY student_id
    """)).fetchall()
    return [dict(zip(r._mapping.keys(), r._mapping.values())) for r in rows]


@router.put("/students/{student_id}/role")
def update_student_role(
    student_id: int,
    role:       str = Form(...),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Change student role — raw SQL UPDATE."""
    require_admin(token, db)
    if role not in ("student", "owner", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    db.execute(
        text("UPDATE Student SET role = :role WHERE student_id = :id"),
        {"role": role, "id": student_id}
    )
    db.commit()
    return {"message": f"Role updated to {role}"}


@router.put("/students/{student_id}/status")
def update_student_status(
    student_id: int,
    status:     str = Form(...),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Suspend or reactivate a student account — raw SQL UPDATE."""
    require_admin(token, db)
    if status not in ("Active", "Suspended", "Locked"):
        raise HTTPException(status_code=400, detail="Invalid status")
    db.execute(
        text("UPDATE Student SET account_status=:s, failed_attempts=0, locked_until=NULL WHERE student_id=:id"),
        {"s": status, "id": student_id}
    )
    db.execute(
        text("INSERT INTO AuditLog (student_id, action, details) VALUES (:id, 'ADMIN_STATUS_CHANGE', :detail)"),
        {"id": student_id, "detail": f"Account status changed to {status} by admin"}
    )
    db.commit()
    return {"message": f"Account status set to {status}"}


@router.delete("/students/{student_id}")
def delete_student(student_id: int, token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """Remove a student — raw SQL DELETE (cascade handled by FK in schema)."""
    require_admin(token, db)
    db.execute(text("DELETE FROM Student WHERE student_id = :id"), {"id": student_id})
    db.commit()
    return {"message": "Student removed"}


@router.get("/vehicles")
def get_all_vehicles(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """
    All vehicles with owner info.
    ✅ Raw SQL JOIN — returns all fields the admin dashboard needs.
    """
    require_admin(token, db)
    rows = db.execute(text("""
        SELECT
            v.vehicle_id,
            v.brand,
            v.model,
            v.vehicle_type,
            v.license_plate,
            v.hourly_rate,
            v.availability_status,
            v.avg_rating,
            v.total_reviews,
            v.is_approved,
            v.location,
            v.fuel_type,
            v.seating_capacity,
            s.full_name   AS owner_name,
            s.email       AS owner_email,
            s.phone       AS owner_phone
        FROM Vehicle v
        JOIN Student s ON v.owner_id = s.student_id
        ORDER BY v.vehicle_id
    """)).fetchall()
    return [dict(zip(r._mapping.keys(), r._mapping.values())) for r in rows]


@router.put("/vehicles/{vehicle_id}/approve")
def approve_vehicle(
    vehicle_id: int,
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Approve a vehicle listing — raw SQL UPDATE."""
    require_admin(token, db)
    db.execute(
        text("UPDATE Vehicle SET is_approved = TRUE WHERE vehicle_id = :vid"),
        {"vid": vehicle_id}
    )
    db.commit()
    return {"message": "Vehicle approved"}


@router.put("/vehicles/{vehicle_id}/status")
def set_vehicle_status(
    vehicle_id: int,
    status:     str = Form(...),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Admin: UPDATE vehicle availability status.
    DBMS: UPDATE — blocks/unblocks vehicles.
    """
    require_admin(token, db)
    allowed = ("Available", "Maintenance")
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {allowed}")
    db.execute(
        text("UPDATE Vehicle SET availability_status = :s WHERE vehicle_id = :vid"),
        {"s": status, "vid": vehicle_id}
    )
    db.execute(
        text("INSERT INTO AuditLog (action, details) VALUES ('ADMIN_VEHICLE_STATUS', :d)"),
        {"d": f"Vehicle #{vehicle_id} status set to {status} by admin"}
    )
    db.commit()
    return {"message": f"Vehicle #{vehicle_id} status set to {status}"}


@router.delete("/vehicles/{vehicle_id}")
def delete_vehicle_admin(
    vehicle_id: int,
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Admin: DELETE any vehicle (hard delete).
    DBMS: DELETE — FK CASCADE removes linked records.
    """
    require_admin(token, db)
    row = db.execute(
        text("SELECT vehicle_id, brand, model FROM Vehicle WHERE vehicle_id = :vid"),
        {"vid": vehicle_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    db.execute(text("DELETE FROM Vehicle WHERE vehicle_id = :vid"), {"vid": vehicle_id})
    db.execute(
        text("INSERT INTO AuditLog (action, details) VALUES ('ADMIN_DELETE_VEHICLE', :d)"),
        {"d": f"Vehicle #{vehicle_id} ({row._mapping['brand']} {row._mapping['model']}) deleted by admin"}
    )
    db.commit()
    return {"message": f"Vehicle #{vehicle_id} deleted successfully"}


@router.get("/rentals")
def get_all_rentals(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """
    All rentals with student and vehicle details.
    ✅ Queries vw_rental_history VIEW.
    """
    require_admin(token, db)
    rows = db.execute(text("SELECT * FROM vw_rental_history ORDER BY rental_id DESC")).fetchall()
    result = []
    for r in rows:
        d = dict(zip(r._mapping.keys(), r._mapping.values()))
        d["vehicle_name"] = f"{d.get('brand', '')} {d.get('model', '')}".strip() or "Vehicle"
        d["renter_name"] = d.get("student_name", "Student")
        result.append(d)
    return result


@router.get("/payments")
def get_all_payments(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """
    All payments.
    ✅ Queries vw_payment_history VIEW.
    """
    require_admin(token, db)
    rows = db.execute(text("SELECT * FROM vw_payment_history ORDER BY payment_id DESC")).fetchall()
    result = []
    for r in rows:
        d = dict(zip(r._mapping.keys(), r._mapping.values()))
        d["renter_name"] = d.get("student_name", "Student")
        result.append(d)
    return result


@router.get("/revenue-report")
def get_revenue_report(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """
    Financial summary and revenue by vehicle type.
    ✅ Aggregated via MySQL SUM and GROUP BY.
    """
    require_admin(token, db)
    tot = db.execute(text("""
        SELECT 
            COALESCE(SUM(CASE WHEN payment_status = 'Completed' THEN amount ELSE 0 END), 0) AS total_revenue,
            COALESCE(SUM(refund_amount), 0) AS total_refunds
        FROM Payment
    """)).fetchone()._mapping

    by_type = db.execute(text("""
        SELECT 
            v.vehicle_type AS type,
            COUNT(DISTINCT r.rental_id) AS rentals,
            COALESCE(SUM(p.amount), 0) AS revenue
        FROM Vehicle v
        JOIN Rental r ON v.vehicle_id = r.vehicle_id
        LEFT JOIN Payment p ON r.rental_id = p.rental_id AND p.payment_status = 'Completed'
        GROUP BY v.vehicle_type
    """)).fetchall()

    return {
        "total_revenue": float(tot["total_revenue"]),
        "total_refunds": float(tot["total_refunds"]),
        "by_type": [
            {
                "type": row._mapping["type"],
                "rentals": int(row._mapping["rentals"]),
                "revenue": float(row._mapping["revenue"])
            }
            for row in by_type
        ]
    }


@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 100,
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Immutable audit log — direct SQL SELECT.
    ✅ Every login, booking, payment, and admin action is logged by MySQL TRIGGERS.
    """
    require_admin(token, db)
    rows = db.execute(
        text("""
            SELECT a.log_id, a.action, a.details, a.timestamp, a.ip_address,
                   s.full_name AS student_name, s.email
            FROM AuditLog a
            LEFT JOIN Student s ON a.student_id = s.student_id
            ORDER BY a.timestamp DESC
            LIMIT :lim
        """),
        {"lim": limit}
    ).fetchall()
    return [dict(zip(r._mapping.keys(), r._mapping.values())) for r in rows]


@router.get("/disputes")
def get_disputes(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """All disputes — direct SQL JOIN."""
    require_admin(token, db)
    rows = db.execute(text("""
        SELECT d.*, s.full_name AS raised_by_name,
               CONCAT(v.brand,' ',v.model) AS vehicle_name
        FROM Dispute d
        JOIN Student s ON d.raised_by = s.student_id
        JOIN Rental  r ON d.rental_id = r.rental_id
        JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
        ORDER BY d.dispute_id DESC
    """)).fetchall()
    return [dict(zip(r._mapping.keys(), r._mapping.values())) for r in rows]


@router.put("/disputes/{dispute_id}/resolve")
def resolve_dispute(
    dispute_id: int,
    resolution: str = Form(...),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Resolve a dispute — raw SQL UPDATE."""
    require_admin(token, db)
    db.execute(
        text("""
            UPDATE Dispute
            SET status='Resolved', resolution=:res, resolved_at=NOW()
            WHERE dispute_id=:did
        """),
        {"res": resolution, "did": dispute_id}
    )
    db.commit()
    return {"message": "Dispute resolved"}


@router.get("/reports/utilization")
def vehicle_report(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """
    Vehicle utilization report.
    ✅ Calls sp_vehicle_utilization_report() stored procedure.
    """
    require_admin(token, db)
    rows = db.execute(text("CALL sp_vehicle_utilization_report()")).fetchall()
    return [dict(zip(r._mapping.keys(), r._mapping.values())) for r in rows]
