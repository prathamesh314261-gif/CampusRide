"""
Coupons routes — 100% SQL-Driven.
Coupon validation via direct SQL query.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
import auth
from database import get_db

router = APIRouter(prefix="/api/coupons", tags=["coupons"])


@router.get("/validate")
def validate_coupon(
    code: str = Query(..., description="Coupon code to validate"),
    subtotal: float = Query(0, description="Rental subtotal to calculate discount"),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Validate a coupon code and calculate discount amount.
    100% SQL-Driven — queries Coupon table directly.
    """
    auth.verify_token(token)  # Just ensure user is authenticated

    row = db.execute(
        text("""
            SELECT coupon_id, code, discount_percentage, valid_from, valid_to, is_active
            FROM Coupon
            WHERE UPPER(code) = UPPER(:code)
              AND is_active = TRUE
              AND CURDATE() BETWEEN valid_from AND valid_to
            LIMIT 1
        """),
        {"code": code.strip()}
    ).fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Invalid or expired coupon code"
        )

    m = row._mapping
    discount_pct = float(m["discount_percentage"])
    discount_amount = round((subtotal * discount_pct) / 100, 2)

    return {
        "valid": True,
        "coupon_id": m["coupon_id"],
        "code": m["code"],
        "discount_percentage": discount_pct,
        "discount_amount": discount_amount,
        "valid_from": str(m["valid_from"]),
        "valid_to": str(m["valid_to"])
    }


@router.get("/validate/{code}")
def validate_coupon_path(
    code: str,
    subtotal: float = Query(0),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Path-parameter alias for coupon validation."""
    return validate_coupon(code=code, subtotal=subtotal, token=token, db=db)


@router.get("")
def list_coupons(db: Session = Depends(get_db)):
    """List all active coupons — for display purposes."""
    rows = db.execute(
        text("""
            SELECT coupon_id, code, discount_percentage, valid_from, valid_to
            FROM Coupon
            WHERE is_active = TRUE AND CURDATE() BETWEEN valid_from AND valid_to
            ORDER BY discount_percentage DESC
        """)
    ).fetchall()
    return [dict(zip(r._mapping.keys(), r._mapping.values())) for r in rows]
