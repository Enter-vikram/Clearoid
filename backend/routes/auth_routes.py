from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session
from database.connection import Base, get_db
import hashlib
import secrets

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Simple User Model
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

# Hash password
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Sign Up
@router.post("/signup", response_model=AuthResponse)
def signup(data: SignUpRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name or data.email.split('@')[0]
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return AuthResponse(
        success=True,
        message="Account created successfully",
        user={"id": user.id, "email": user.email, "name": user.name}
    )

# Sign In
@router.post("/signin", response_model=AuthResponse)
def signin(data: SignInRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    
    if not user or user.password_hash != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return AuthResponse(
        success=True,
        message="Signed in successfully",
        user={"id": user.id, "email": user.email, "name": user.name}
    )

# Check if logged in
@router.get("/me")
def get_current_user(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "name": user.name}
