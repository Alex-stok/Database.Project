# app/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from decimal import Decimal

# =====================================================
# AUTH / USER
# =====================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    # Optional org info during registration
    org_name: Optional[str] = None
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


# =====================================================
# ORGANIZATION + PROFILE
# =====================================================

class OrgOut(BaseModel):
    org_id: int
    name: str
    industry: Optional[str] = None
    address: Optional[str] = None
    size: Optional[str] = None

    class Config:
        from_attributes = True


class ProfileOut(BaseModel):
    user: UserOut
    organization: Optional[OrgOut]


class ProfileUpdate(BaseModel):
    """
    Used by PUT /api/profile/me

    All fields are optional so the user can update just one field
    without sending everything.
    """
    full_name: Optional[str] = None

    # Org fields (we'll create/update the org behind the scenes)
    org_name: Optional[str] = None
    industry: Optional[str] = None
    address: Optional[str] = None
    size: Optional[str] = None


# =====================================================
# ACTIVITIES
# =====================================================

class ActivityCreate(BaseModel):
    """
    If any endpoint uses a typed body for creating activities,
    this matches the structured ActivityLog fields.
    """
    facility_id: int
    activity_type_id: int
    unit_id: int
    quantity: Decimal
    activity_date: date


# =====================================================
# EMISSION FACTORS
# =====================================================

class FactorOut(BaseModel):
    factor_id: int
    source: str
    category: str
    unit: str
    factor: Decimal
    year: Optional[int] = None

    class Config:
        from_attributes = True
