import hashlib

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session

from database.connection import Base, get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


# User Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)


# Schemas
class SignUpRequest(BaseModel):
    email: str
    password: str
    name: str = None


class SignInRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    user: dict = None


def _is_legacy_sha256(stored: str) -> bool:
    """Return True if the stored hash is a plain SHA256 hex (pre-bcrypt)."""
    return len(stored) == 64 and all(c in "0123456789abcdef" for c in stored)


def _sha256_hex(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, stored: str) -> bool:
    """
    Verify against bcrypt hash.
    Also accepts legacy SHA256 hashes so existing users are not locked out.
    """
    if _is_legacy_sha256(stored):
        return _sha256_hex(password) == stored
    try:
        return bcrypt.checkpw(password.encode(), stored.encode())
    except Exception:
        return False


@router.post("/signup", response_model=AuthResponse)
def signup(data: SignUpRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name or data.email.split("@")[0],
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return AuthResponse(
        success=True,
        message="Account created successfully",
        user={"id": user.id, "email": user.email, "name": user.name},
    )


@router.post("/signin", response_model=AuthResponse)
def signin(data: SignInRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Transparent rehash: upgrade legacy SHA256 hash to bcrypt on successful login
    if _is_legacy_sha256(user.password_hash):
        user.password_hash = hash_password(data.password)
        db.commit()

    return AuthResponse(
        success=True,
        message="Signed in successfully",
        user={"id": user.id, "email": user.email, "name": user.name},
    )


@router.get("/me")
def get_current_user(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "name": user.name}
