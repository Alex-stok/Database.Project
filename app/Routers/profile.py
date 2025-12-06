# app/Routers/profile.py
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import get_current_user
from ..models import User, Organization
from ..schemas import ProfileOut, ProfileUpdate

router = APIRouter(prefix="/api/profile", tags=["profile"])
pages = APIRouter(tags=["profile:pages"])


@pages.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "profile.html",
        {"request": request},
    )


@router.get("/me", response_model=ProfileOut)
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org = None
    if user.org_id:
        org = db.query(Organization).filter(Organization.org_id == user.org_id).first()
    return {"user": user, "organization": org}


@router.put("/me", response_model=ProfileOut)
def update_me(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Update user name
    if payload.full_name is not None:
        user.full_name = payload.full_name

    # Update or create org if any org fields provided
    fields_present = any(
        [
            payload.org_name,
            payload.org_industry,
            payload.org_address,
            payload.org_size,
        ]
    )

    org = None
    if fields_present:
        if user.org_id:
            org = db.query(Organization).filter(Organization.org_id == user.org_id).first()
        if not org:
            org = Organization()
            db.add(org)
            db.flush()
            user.org_id = org.org_id

        if payload.org_name is not None:
            org.name = payload.org_name
        if payload.org_industry is not None:
            org.industry = payload.org_industry
        if payload.org_address is not None:
            org.address = payload.org_address
        if payload.org_size is not None:
            org.size = payload.org_size

    db.commit()
    db.refresh(user)
    if org:
        db.refresh(org)

    return {"user": user, "organization": org}
