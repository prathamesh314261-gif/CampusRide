"""
Authentication module for CampusRide — 100% SQL-Driven.
Handles JWT token generation and verification only.
All password logic lives in MySQL (fn_hash_password).
"""
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text
from database import SessionLocal

# Secret key for JWT (in production, use env variable)
SECRET_KEY = "campusride-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


# Password hashing is handled by MySQL fn_hash_password() — not Python
# Kept as a no-op for any legacy import compatibility
def hash_password(password: str) -> str:
    """Deprecated: Use MySQL fn_hash_password() via sp_register()."""
    return password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Deprecated: Use MySQL sp_login() for authentication."""
    return False


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    # JWT requires sub to be a string
    if "sub" in to_encode and not isinstance(to_encode["sub"], str):
        to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(lambda: SessionLocal())):
    """Get current authenticated user via raw SQL — no ORM."""
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    try:
        payload = verify_token(token)
        student_id_str = payload.get("sub")
        if student_id_str is None:
            raise credentials_exception
        student_id = int(student_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
    row = db.execute(text("SELECT * FROM Student WHERE student_id = :id"), {"id": student_id}).fetchone()
    if row is None:
        raise credentials_exception
    return row._mapping


def require_admin(token: str = Depends(oauth2_scheme), db=Depends(lambda: SessionLocal())):
    """Dependency to enforce admin role — raw SQL."""
    user = get_current_user(token, db)
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin authorization required")
    return user


def log_audit(db, action: str, student_id: int = None, details: str = "", ip_address: str = "127.0.0.1"):
    """Record security event in AuditLog — raw SQL INSERT."""
    try:
        db.execute(
            text("INSERT INTO AuditLog (student_id, action, details, ip_address) VALUES (:sid, :action, :details, :ip)"),
            {"sid": student_id, "action": action, "details": details, "ip": ip_address}
        )
        db.commit()
    except Exception:
        db.rollback()

