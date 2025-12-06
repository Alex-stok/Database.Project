# app/schemas.py
from pydantic import BaseModel, EmailStr
from decimal import Decimal
from typing import Optional

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


# ---------- Activities ----------

class ActivityCreate(BaseModel):
    facility_id: int
    activity_type: str   # e.g. "ELEC_USE", "NAT_GAS" (from activity_type.code)
    quantity: float
    unit: str            # e.g. "kWh", "therm", "gal"
    # keep as str/Decimal if you want, but date is more natural:
    # from datetime import date
    # activity_date: date
    activity_date: Decimal


# ---------- Emission factors ----------

class FactorOut(BaseModel):
    factor_id: int
    source: str
    category: str
    unit: str
    factor: Decimal
    year: Optional[int] = None

    class Config:
        from_attributes = True
