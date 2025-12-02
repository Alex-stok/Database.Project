from pydantic import BaseModel, EmailStr
from decimal import Decimal 
from typing import Optional

# Auth
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    org_name: Optional[str] = None  # allow creating org at registration
    industry: Optional[str] = None
    size: Optional[str] = None

class UserOut(BaseModel):
    user_id: int
    email: EmailStr
    full_name: Optional[str]
    role: str
    org_id: Optional[int]
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ActivityCreate(BaseModel):
    facility_id: int
    activity_type: str
    quantity: float
    unit: str
    activity_date: date

