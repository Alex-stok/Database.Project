# app/Routers/profile.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Organization
from ..security import get_current_user

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/api/profile", tags=["profile"])

# ---------- API: return current user + org (for page population) ----------
@router.get("/me")
def get_me(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    org = db.query(Organization).filter(Organization.org_id == user.org_id).first() if user.org_id else None
    return {
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "org_id": user.org_id,
        },
        "organization": None if not org else {
            "org_id": org.org_id,
            "name": org.name,
            "industry": org.industry,
            "address": org.address,
            "size": org.size,
        }
    }

# ---------- API: update user basic fields ----------
class UserUpdatePayload:
    full_name: str | None = None
    role: str | None = None

from pydantic import BaseModel
class ProfileUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    org_name: str | None = None
    org_industry: str | None = None
    org_address: str | None = None
    org_size: str | None = None

@router.put("/me")
def update_me(payload: ProfileUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Update user
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        user.role = payload.role

    # Update or create org (if user belongs to one)
    org = None
    if user.org_id:
        org = db.query(Organization).filter(Organization.org_id == user.org_id).first()
    if not org and (payload.org_name or payload.org_industry or payload.org_address or payload.org_size):
        org = Organization(name=payload.org_name or "Organization")
        db.add(org)
        db.flush()
        user.org_id = org.org_id

    if org:
        if payload.org_name is not None: org.name = payload.org_name
        if payload.org_industry is not None: org.industry = payload.org_industry
        if payload.org_address is not None: org.address = payload.org_address
        if payload.org_size is not None: org.size = payload.org_size

    db.commit()
    return {"ok": True}

# ---------- PAGE route (keeps your pattern) ----------
@router.get("/page", response_class=HTMLResponse)
def profile_page(request: Request, user: User = Depends(get_current_user)):
    # This renders templates/profile.html
    return templates.TemplateResponse("profile.html", {"request": request})
