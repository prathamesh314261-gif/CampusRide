"""
Maintenance routes — 100% SQL-Driven.
Add maintenance via sp_add_maintenance() stored procedure.
MySQL TRIGGER trg_after_maintenance_insert auto-sets vehicle to 'Maintenance'.
MySQL TRIGGER trg_after_maintenance_done auto-sets vehicle back to 'Available'.
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import auth
from database import get_db

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


@router.post("")
def report_maintenance(
    vehicle_id:       int = Form(...),
    maintenance_type: str = Form(...),
    description:      Optional[str] = Form(None),
    maintenance_date: Optional[str] = Form(None),
    cost:             float = Form(0.0),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Schedule maintenance.
    ✅ Calls sp_add_maintenance() stored procedure.
    MySQL TRIGGER trg_after_maintenance_insert auto-marks vehicle as 'Maintenance'.
    """
    from datetime import date
    payload = auth.verify_token(token)

    m_date = maintenance_date or str(date.today())

    db.execute(text("SET @p_status = ''"))
    db.execute(
        text("CALL sp_add_maintenance(:vid, :type, :desc, :cost, :date, @p_status)"),
        {
            "vid":  vehicle_id,
            "type": maintenance_type,
            "desc": description or "",
            "cost": cost,
            "date": m_date
        }
    )
    status_row = db.execute(text("SELECT @p_status")).fetchone()
    sp_status  = status_row[0] if status_row else "ERROR"
    db.commit()

    if sp_status != "OK":
        raise HTTPException(status_code=500, detail="Failed to schedule maintenance")

    return {"message": "Maintenance scheduled. Vehicle marked as 'Maintenance' automatically by database trigger."}


@router.get("/my")
def get_my_maintenance(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get maintenance records for owner's vehicles.
    ✅ Queries vw_active_maintenance VIEW + raw SQL JOIN for history.
    """
    payload    = auth.verify_token(token)
    student_id = int(payload.get("sub"))

    rows = db.execute(
        text("""
            SELECT m.maintenance_id, m.vehicle_id,
                   CONCAT(v.brand, ' ', v.model) AS vehicle_name,
                   v.license_plate,
                   m.maintenance_type, m.description,
                   m.cost, m.maintenance_date, m.status
            FROM Maintenance m
            JOIN Vehicle v ON m.vehicle_id = v.vehicle_id
            WHERE v.owner_id = :oid
            ORDER BY m.maintenance_id DESC
        """),
        {"oid": student_id}
    ).fetchall()
    return [dict(zip(r._mapping.keys(), r._mapping.values())) for r in rows]


@router.get("/vehicle/{vehicle_id}")
def get_vehicle_maintenance(vehicle_id: int, db: Session = Depends(get_db)):
    """Get maintenance history for a specific vehicle — direct SQL."""
    rows = db.execute(
        text("SELECT * FROM Maintenance WHERE vehicle_id = :vid ORDER BY maintenance_id DESC"),
        {"vid": vehicle_id}
    ).fetchall()
    return [dict(zip(r._mapping.keys(), r._mapping.values())) for r in rows]


@router.put("/{maintenance_id}/complete")
def complete_maintenance(
    maintenance_id: int,
    cost: float = Form(0),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Mark maintenance as done.
    ✅ Raw SQL UPDATE triggers trg_after_maintenance_done which auto-frees the vehicle.
    """
    auth.verify_token(token)

    db.execute(
        text("UPDATE Maintenance SET status='Done', cost=:cost WHERE maintenance_id=:mid"),
        {"cost": cost, "mid": maintenance_id}
    )
    # The SQL TRIGGER trg_after_maintenance_done fires automatically
    # and sets Vehicle.availability_status = 'Available'
    db.commit()
    return {"message": "Maintenance completed. Vehicle freed automatically by database trigger."}
