# app/schemas.py
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr


# ---------- Auth ----------
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


# ---------- Activities / Factors ----------
class ActivityCreate(BaseModel):
    facility_id: int
    activity_type_id: int
    unit_id: int
    quantity: Decimal
    activity_date: str  # ISO date string (YYYY-MM-DD)


class FactorOut(BaseModel):
    factor_id: int
    source: Optional[str]
    category: str
    unit: str
    factor: Decimal
    year: Optional[int]

    class Config:
        from_attributes = True


# ---------- Organization & Profile ----------
class OrganizationOut(BaseModel):
    org_id: int
    name: Optional[str]
    industry: Optional[str]
    address: Optional[str]
    size: Optional[str]

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    org_name: Optional[str] = None
    org_industry: Optional[str] = None
    org_address: Optional[str] = None
    org_size: Optional[str] = None


class ProfileOut(BaseModel):
    user: UserOut
    organization: Optional[OrganizationOut]
