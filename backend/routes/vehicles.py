"""
Vehicle routes — 100% SQL-Driven.
Listing, adding, and updating vehicles via raw SQL and stored procedures.
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
import auth

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


@router.get("")
def get_vehicles(db: Session = Depends(get_db)):
    """
    Get all available vehicles with owner info.
    ✅ Queries vw_available_vehicles VIEW — no ORM.
    """
    rows = db.execute(text("SELECT * FROM vw_available_vehicles")).fetchall()
    return [dict(zip(r._mapping.keys(), r._mapping.values())) for r in rows]


@router.get("/all")
def get_all_vehicles(db: Session = Depends(get_db)):
    """Get all vehicles regardless of status — raw SQL JOIN."""
    rows = db.execute(text("""
        SELECT v.*, s.full_name AS owner_name, s.phone AS owner_phone
        FROM Vehicle v
        JOIN Student s ON v.owner_id = s.student_id
        ORDER BY v.vehicle_id
    """)).fetchall()
    return [dict(zip(r._mapping.keys(), r._mapping.values())) for r in rows]


@router.get("/my")
def get_my_vehicles(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """Owner: get vehicles I listed. Direct SQL query."""
    payload    = auth.verify_token(token)
    student_id = int(payload.get("sub"))
    rows = db.execute(
        text("SELECT * FROM Vehicle WHERE owner_id = :oid ORDER BY vehicle_id DESC"),
        {"oid": student_id}
    ).fetchall()
    return [dict(zip(r._mapping.keys(), r._mapping.values())) for r in rows]


@router.get("/my/earnings")
def get_my_earnings(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """
    Owner earnings + stats summary.
    Returns: vehicles_listed, total_earnings, active_rentals, completed_rentals.
    ✅ Direct SQL aggregation — no ORM.
    """
    payload    = auth.verify_token(token)
    student_id = int(payload.get("sub"))

    # Total vehicles listed
    vehicles_listed = db.execute(
        text("SELECT COUNT(*) AS cnt FROM Vehicle WHERE owner_id = :oid"),
        {"oid": student_id}
    ).fetchone()._mapping["cnt"]

    # Earnings and rental counts from completed rentals
    stats = db.execute(
        text("""
            SELECT
                COALESCE(SUM(r.final_amount), 0) AS total_earnings,
                COUNT(r.rental_id)               AS total_rentals,
                COALESCE(AVG(r.final_amount), 0) AS avg_earning
            FROM Rental r
            JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
            WHERE v.owner_id = :oid AND r.status = 'Completed'
        """),
        {"oid": student_id}
    ).fetchone()._mapping

    # Active rentals on owner's vehicles
    active = db.execute(
        text("""
            SELECT COUNT(*) AS cnt FROM Rental r
            JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
            WHERE v.owner_id = :oid AND r.status IN ('Confirmed','Active')
        """),
        {"oid": student_id}
    ).fetchone()._mapping["cnt"]

    return {
        "owner_id":         student_id,
        "vehicles_listed":  int(vehicles_listed),
        "total_earnings":   float(stats["total_earnings"]),
        "total_rentals":    int(stats["total_rentals"]),
        "avg_earning":      float(stats["avg_earning"]),
        "active_rentals":   int(active),
        "completed_rentals": int(stats["total_rentals"])
    }


@router.get("/{vehicle_id}")
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """Get single vehicle details with owner info."""
    row = db.execute(
        text("""
            SELECT v.*, s.full_name AS owner_name, s.phone AS owner_phone
            FROM Vehicle v JOIN Student s ON v.owner_id = s.student_id
            WHERE v.vehicle_id = :vid
        """),
        {"vid": vehicle_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return dict(zip(row._mapping.keys(), row._mapping.values()))


@router.post("")
def add_vehicle(
    vehicle_type:   str = Form(...),
    brand:          str = Form(...),
    model:          str = Form(...),
    seating_capacity: int = Form(2),
    fuel_type:      str = Form(...),
    hourly_rate:    float = Form(...),
    license_plate:  str = Form(...),
    location:       str = Form("Campus Main Gate"),
    description:    str = Form(""),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Add a new vehicle.
    ✅ Calls sp_add_vehicle() stored procedure.
    """
    payload    = auth.verify_token(token)
    student_id = int(payload.get("sub"))

    db.execute(text("SET @p_status = ''"))
    db.execute(
        text("CALL sp_add_vehicle(:oid, :type, :brand, :model, :seats, :fuel, :rate, :plate, :loc, :desc, @p_status)"),
        {
            "oid":   student_id,
            "type":  vehicle_type,
            "brand": brand,
            "model": model,
            "seats": seating_capacity,
            "fuel":  fuel_type,
            "rate":  hourly_rate,
            "plate": license_plate.upper(),
            "loc":   location,
            "desc":  description
        }
    )
    status_row = db.execute(text("SELECT @p_status")).fetchone()
    sp_status  = status_row[0] if status_row else "ERROR"
    db.commit()

    if sp_status == "ERROR_DUPLICATE_PLATE":
        raise HTTPException(status_code=400, detail="A vehicle with this license plate already exists")
    elif sp_status != "OK":
        raise HTTPException(status_code=500, detail="Failed to add vehicle")

    return {"message": f"Vehicle {brand} {model} listed successfully!"}


@router.put("/{vehicle_id}")
def update_vehicle(
    vehicle_id:   int,
    hourly_rate:  Optional[float] = Form(None),
    location:     Optional[str]   = Form(None),
    description:  Optional[str]   = Form(None),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Update vehicle details — raw SQL UPDATE."""
    payload    = auth.verify_token(token)
    student_id = int(payload.get("sub"))

    row = db.execute(
        text("SELECT owner_id FROM Vehicle WHERE vehicle_id = :vid"),
        {"vid": vehicle_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if row._mapping["owner_id"] != student_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    db.execute(
        text("""
            UPDATE Vehicle SET
                hourly_rate  = IFNULL(:rate, hourly_rate),
                location     = IFNULL(:loc,  location),
                description  = IFNULL(:desc, description)
            WHERE vehicle_id = :vid
        """),
        {"rate": hourly_rate, "loc": location, "desc": description, "vid": vehicle_id}
    )
    db.commit()
    return {"message": "Vehicle updated successfully"}


@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: int, token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """Delete a vehicle (owner only) — raw SQL DELETE."""
    payload    = auth.verify_token(token)
    student_id = int(payload.get("sub"))

    row = db.execute(
        text("SELECT owner_id FROM Vehicle WHERE vehicle_id = :vid"),
        {"vid": vehicle_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if row._mapping["owner_id"] != student_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    db.execute(text("DELETE FROM Vehicle WHERE vehicle_id = :vid"), {"vid": vehicle_id})
    db.commit()
    return {"message": "Vehicle removed"}
