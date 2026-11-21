"""
Authentication routes — 100% SQL-Driven.
All login, register, and password logic runs via MySQL Stored Procedures.
Python only handles JWT token creation (which must stay in app layer for security).
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from datetime import timedelta
import auth

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(
    email:    str = Form(None),
    username: str = Form(None),
    password: str = Form(...),
    login_as: str = Form("renter"),
    db: Session = Depends(get_db)
):
    """
    100% SQL-Driven Login.
    Calls MySQL Stored Procedure: sp_login(email, password, @status)
    All validation (lockout, suspension, brute-force) happens inside MySQL.
    """
    login_email = (email or username or "").strip().lower()
    if not login_email:
        raise HTTPException(status_code=422, detail="Email is required")

    # Validate login_as
    if login_as not in ["owner", "renter", "admin"]:
        login_as = "renter"

    # ✅ Call the MySQL Stored Procedure — all auth logic is in SQL
    db.execute(text("SET @p_status = ''"))
    db.execute(
        text("CALL sp_login(:email, :password, @p_status)"),
        {"email": login_email, "password": password}
    )

    # Get the OUT parameter
    status_row = db.execute(text("SELECT @p_status AS status")).fetchone()
    sp_status  = status_row[0] if status_row else "NOT_FOUND"

    # Get the student record returned by the procedure
    student_row = db.execute(
        text("SELECT * FROM Student WHERE email = :e"),
        {"e": login_email}
    ).fetchone()

    # Map SQL procedure status to HTTP responses
    if sp_status == "NOT_FOUND":
        raise HTTPException(status_code=401, detail="Invalid email or password")
    elif sp_status == "SUSPENDED":
        raise HTTPException(status_code=403, detail="Account suspended. Contact admin.")
    elif sp_status == "LOCKED":
        raise HTTPException(status_code=403, detail="Account locked due to too many failed attempts. Try again in 15 minutes.")
    elif sp_status == "BAD_PASSWORD":
        attempts = student_row._mapping.get("failed_attempts", 0) if student_row else 0
        remaining = max(0, 5 - attempts)
        raise HTTPException(status_code=401, detail=f"Invalid password. {remaining} attempt(s) remaining before lockout.")
    elif sp_status != "OK":
        raise HTTPException(status_code=500, detail="Authentication error")

    # Auto-promote role for admin users
    db_role = student_row._mapping.get("role", "student")
    if db_role == "admin":
        login_as = "admin"

    # Create JWT token (stays in Python — tokens are app-layer, not DB-layer)
    token = auth.create_access_token(
        data={
            "sub":      str(student_row._mapping["student_id"]),
            "role":     db_role,
            "login_as": login_as
        },
        expires_delta=timedelta(hours=24)
    )

    return {
        "access_token": token,
        "token_type":   "bearer",
        "student_id":   student_row._mapping["student_id"],
        "full_name":    student_row._mapping["full_name"],
        "roll_number":  student_row._mapping.get("roll_number") or "N/A",
        "role":         db_role,
        "login_as":     login_as
    }


@router.post("/register")
def register(
    full_name:  str = Form(...),
    email:      str = Form(...),
    phone:      str = Form(...),
    department: str = Form(...),
    hostel:     str = Form(...),
    password:   str = Form(...),
    roll_number: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    100% SQL-Driven Registration.
    Calls MySQL Stored Procedure: sp_register(...)
    Duplicate check, password hashing, roll generation all done by MySQL.
    """
    clean_email = email.strip().lower()

    # Domain validation (lightweight — stays in API layer)
    allowed_domains = ["@vit.edu", ".vit.edu", "@campus.edu", "@college.edu"]
    if not any(clean_email.endswith(d) for d in allowed_domains):
        raise HTTPException(
            status_code=400,
            detail="Registration restricted to campus members only. Use your @vit.edu email."
        )

    # ✅ Call MySQL Stored Procedure — all DB logic inside SQL
    db.execute(text("SET @p_status = ''"))
    db.execute(
        text("CALL sp_register(:name, :email, :phone, :dept, :hostel, :pwd, :roll, @p_status)"),
        {
            "name":   full_name,
            "email":  clean_email,
            "phone":  phone,
            "dept":   department,
            "hostel": hostel,
            "pwd":    password,
            "roll":   roll_number
        }
    )

    status_row = db.execute(text("SELECT @p_status")).fetchone()
    sp_status  = status_row[0] if status_row else "ERROR"

    if sp_status == "DUPLICATE_EMAIL":
        raise HTTPException(status_code=400, detail="Email already registered")
    elif sp_status != "OK":
        raise HTTPException(status_code=500, detail="Registration failed")

    db.commit()

    # Fetch the newly created student
    student = db.execute(
        text("SELECT * FROM Student WHERE email = :e"), {"e": clean_email}
    ).fetchone()

    return {
        "message":    "Account created successfully!",
        "student_id": student._mapping["student_id"],
        "full_name":  student._mapping["full_name"],
        "roll_number":student._mapping.get("roll_number") or "N/A",
        "role":       student._mapping["role"]
    }


@router.get("/me")
def get_profile(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """Get current user profile — direct SQL query, no ORM."""
    payload    = auth.verify_token(token)
    student_id = int(payload.get("sub"))

    # ✅ Direct SQL query — no Python ORM models
    row = db.execute(
        text("SELECT * FROM Student WHERE student_id = :id"),
        {"id": student_id}
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Student not found")

    m = row._mapping
    return {
        "student_id": m["student_id"],
        "full_name":  m["full_name"],
        "roll_number":m.get("roll_number") or "",
        "email":      m["email"],
        "phone":      m["phone"],
        "department": m["department"],
        "hostel":     m["hostel"],
        "role":       m["role"],
        "bio":        m.get("bio") or "",
        "trust_score":float(m.get("trust_score") or 5.0)
    }


@router.get("/profile")
def get_my_profile(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """Alias for /me."""
    return get_profile(token, db)


@router.put("/profile")
def update_profile(
    full_name:   str = Form(None),
    roll_number: str = Form(None),
    phone:       str = Form(None),
    department:  str = Form(None),
    hostel:      str = Form(None),
    bio:         str = Form(None),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Update profile — raw SQL UPDATE, no ORM."""
    payload    = auth.verify_token(token)
    student_id = int(payload.get("sub"))

    # ✅ Raw SQL UPDATE — no ORM
    db.execute(
        text("""
            UPDATE Student SET
                full_name   = IFNULL(:name,  full_name),
                roll_number = IFNULL(:roll,  roll_number),
                phone       = IFNULL(:phone, phone),
                department  = IFNULL(:dept,  department),
                hostel      = IFNULL(:hostel,hostel),
                bio         = IFNULL(:bio,   bio)
            WHERE student_id = :id
        """),
        {
            "name":   full_name,
            "roll":   roll_number.strip().upper() if roll_number else None,
            "phone":  phone,
            "dept":   department,
            "hostel": hostel,
            "bio":    bio,
            "id":     student_id
        }
    )
    db.commit()
    return {"message": "Profile updated successfully"}


@router.post("/logout")
def logout(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """Logout — log it directly in AuditLog via raw SQL."""
    try:
        payload    = auth.verify_token(token)
        student_id = int(payload.get("sub"))
        db.execute(
            text("INSERT INTO AuditLog (student_id, action, details) VALUES (:id, 'LOGOUT', 'User logged out')"),
            {"id": student_id}
        )
        db.commit()
    except Exception:
        pass
    return {"message": "Logged out successfully"}
