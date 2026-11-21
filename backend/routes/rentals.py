"""
Rental routes — 100% SQL-Driven.
All booking, completion, and cancellation logic handled by MySQL Stored Procedures.
Python is only a thin REST gateway — zero business logic here.
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
import auth
from datetime import datetime

router = APIRouter(prefix="/api/rentals", tags=["rentals"])


@router.post("")
def create_rental(
    vehicle_id:      int = Form(...),
    start_time:      str = Form(...),
    end_time:        str = Form(...),
    pickup_location: str = Form(...),
    return_location: str = Form("Same as pickup"),
    coupon_code:     Optional[str] = Form(None),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    100% SQL-Driven Booking.
    Calls MySQL Stored Procedure: sp_create_rental(...)
    All math (hours, subtotal, discount, final_amount) computed inside MySQL.
    MySQL TRIGGER trg_before_rental_insert prevents double-booking.
    MySQL TRIGGER trg_after_rental_insert auto-marks vehicle as 'Rented'.
    """
    payload    = auth.verify_token(token)
    student_id = int(payload.get("sub"))

    # Parse and validate datetimes (stays in API layer — type safety)
    try:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '').split('+')[0])
        end_dt   = datetime.fromisoformat(end_time.replace('Z', '').split('+')[0])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format")

    if end_dt <= start_dt:
        raise HTTPException(status_code=400, detail="Return time must be after pickup time")

    # ✅ Call MySQL Stored Procedure — ALL business logic inside SQL
    db.execute(text("SET @p_status = ''"))
    db.execute(
        text("CALL sp_create_rental(:sid, :vid, :start, :end, :pickup, :ret, :coupon, @p_status)"),
        {
            "sid":    student_id,
            "vid":    vehicle_id,
            "start":  start_dt,
            "end":    end_dt,
            "pickup": pickup_location,
            "ret":    return_location,
            "coupon": coupon_code or ""
        }
    )

    status_row = db.execute(text("SELECT @p_status")).fetchone()
    sp_status  = status_row[0] if status_row else "ERROR"

    if sp_status == "NOT_AVAILABLE":
        raise HTTPException(status_code=400, detail="Vehicle is currently not available")
    elif sp_status != "OK":
        raise HTTPException(status_code=500, detail="Booking failed. Please try again.")

    db.commit()

    # Fetch the new rental
    rental = db.execute(
        text("SELECT * FROM Rental WHERE student_id=:sid AND vehicle_id=:vid ORDER BY rental_id DESC LIMIT 1"),
        {"sid": student_id, "vid": vehicle_id}
    ).fetchone()

    m = rental._mapping
    return {
        "message":      "Rental booked successfully!",
        "rental_id":    m["rental_id"],
        "vehicle_id":   m["vehicle_id"],
        "total_hours":  float(m["total_hours"]),
        "subtotal":     float(m["subtotal"]),
        "discount":     float(m.get("discount") or 0),
        "final_amount": float(m["final_amount"]),
        "status":       m["status"],
        "pickup_code":  m.get("pickup_code") or "N/A"
    }


@router.get("")
def get_my_rentals(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get all rentals for the logged-in student.
    ✅ Queries vw_rental_history VIEW directly — no ORM joins.
    """
    payload    = auth.verify_token(token)
    student_id = int(payload.get("sub"))

    rows = db.execute(
        text("SELECT * FROM vw_rental_history WHERE student_id = :sid ORDER BY rental_id DESC"),
        {"sid": student_id}
    ).fetchall()

    return [dict(zip(r._mapping.keys(), r._mapping.values())) for r in rows]


@router.get("/owner")
def get_owner_rentals(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get all rentals on vehicles owned by the current user.
    ✅ Direct SQL join — no ORM models.
    """
    payload    = auth.verify_token(token)
    student_id = int(payload.get("sub"))

    rows = db.execute(
        text("""
            SELECT r.*, CONCAT(v.brand, ' ', v.model) AS vehicle_name,
                   v.vehicle_type, v.license_plate,
                   s.full_name AS renter_name, s.phone AS renter_phone
            FROM Rental r
            JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
            JOIN Student s ON r.student_id = s.student_id
            WHERE v.owner_id = :oid
            ORDER BY r.rental_id DESC
        """),
        {"oid": student_id}
    ).fetchall()

    return [dict(zip(r._mapping.keys(), r._mapping.values())) for r in rows]


@router.put("/{rental_id}/end")
def end_rental(rental_id: int, token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """
    Complete a rental.
    ✅ Calls sp_complete_rental() — SQL trigger auto-frees the vehicle.
    """
    payload    = auth.verify_token(token)
    student_id = int(payload.get("sub"))

    # Verify ownership
    row = db.execute(text("SELECT student_id FROM Rental WHERE rental_id = :rid"), {"rid": rental_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Rental not found")
    if row._mapping["student_id"] != student_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    db.execute(text("SET @p_status = ''"))
    db.execute(text("CALL sp_complete_rental(:rid, @p_status)"), {"rid": rental_id})
    status_row = db.execute(text("SELECT @p_status")).fetchone()
    sp_status  = status_row[0] if status_row else "ERROR"
    db.commit()

    if sp_status == "ALREADY_DONE":
        raise HTTPException(status_code=400, detail="Rental already completed or cancelled")
    return {"message": "Rental completed. Vehicle is now available."}


@router.put("/{rental_id}/cancel")
def cancel_rental(
    rental_id: int,
    reason:    Optional[str] = Form(None),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Cancel a rental.
    ✅ Calls sp_cancel_rental() — SQL trigger auto-frees the vehicle.
    """
    payload    = auth.verify_token(token)
    student_id = int(payload.get("sub"))

    db.execute(text("SET @p_status = ''"))
    db.execute(
        text("CALL sp_cancel_rental(:rid, :sid, :reason, @p_status)"),
        {"rid": rental_id, "sid": student_id, "reason": reason or "Cancelled by user"}
    )
    status_row = db.execute(text("SELECT @p_status")).fetchone()
    sp_status  = status_row[0] if status_row else "ERROR"
    db.commit()

    if sp_status == "FORBIDDEN":
        raise HTTPException(status_code=403, detail="Unauthorized to cancel this rental")
    return {"message": "Rental cancelled successfully"}


@router.put("/{rental_id}/start")
def start_rental(
    rental_id: int,
    otp:       Optional[str] = Form(None),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Mark rental as Active (after OTP handover). Direct SQL UPDATE."""
    payload    = auth.verify_token(token)
    student_id = int(payload.get("sub"))

    rental = db.execute(
        text("SELECT * FROM Rental WHERE rental_id = :rid"), {"rid": rental_id}
    ).fetchone()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    if rental._mapping["status"] != "Confirmed":
        raise HTTPException(status_code=400, detail="Rental is not in Confirmed state")

    db.execute(
        text("UPDATE Rental SET status='Active' WHERE rental_id = :rid"),
        {"rid": rental_id}
    )
    db.execute(
        text("INSERT INTO AuditLog (student_id, action, details) VALUES (:sid, 'START_RENTAL', :detail)"),
        {"sid": student_id, "detail": f"Rental #{rental_id} started by student #{student_id}"}
    )
    db.commit()
    return {"message": "Rental started. Drive safely!", "status": "Active"}
