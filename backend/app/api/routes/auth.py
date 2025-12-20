"""
Authentication routes and logic.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from app.db.database import get_db
from app.db.models import User
from passlib.context import CryptContext
from typing import Optional
from datetime import datetime

router = APIRouter()
# Using argon2 instead of bcrypt - more secure and no length limitations
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    created_at: Optional[str] = None  # Changed from datetime to str
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to handle datetime serialization"""
        data = {
            'id': obj.id,
            'email': obj.email,
            'full_name': obj.full_name,
            'created_at': obj.created_at.isoformat() if obj.created_at else None
        }
        return cls(**data)

def verify_password(plain_password, hashed_password):
    """Verify a password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash a password using argon2."""
    return pwd_context.hash(password)

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password, full_name=user.full_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return UserResponse.from_orm(db_user)

@router.post("/login", response_model=UserResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    return UserResponse.from_orm(db_user)
