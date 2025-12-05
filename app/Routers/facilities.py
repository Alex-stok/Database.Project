# app/Routers/facilities.py
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from ..database import get_db
from ..security import get_current_user
from ..models import Facility

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/api/facilities", tags=["facilities"])
pages = APIRouter(tags=["pages"])

# ---------- Pydantic payloads ----------
class FacilityCreate(BaseModel):
    name: str
    location: Optional[str] = None
    grid_region_code: Optional[str] = None

class FacilityOut(BaseModel):
    facility_id: int
    name: str
    location: Optional[str] = None
    grid_region_code: Optional[str] = None
    class Config:
        from_attributes = True

# ---------- JSON API ----------

@router.get("/facilities")
def list_facilities(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Only facilities for the current user's org
    return (
        db.query(Facility)
        .filter(Facility.org_id == user.org_id)
        .order_by(Facility.facility_id)
        .all()
    )


@router.post("/facilities")
def create_facility(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    name = (payload.get("name") or "").strip()
    grid_region_code = (payload.get("grid_region_code") or "").strip()
    location = (payload.get("location") or "").strip()

    if not name:
        raise HTTPException(status_code=400, detail="Facility name is required")

    fac = Facility(
        org_id=user.org_id,
        name=name,
        grid_region_code=grid_region_code or None,
        location=location or None,
    )
    db.add(fac)
    db.commit()
    db.refresh(fac)
    return fac

@router.get("/{facility_id}")
def get_facility(facility_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    f = (
        db.query(Facility)
        .filter(Facility.facility_id == facility_id, Facility.org_id == user.org_id)
        .first()
    )
    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return {
        "facility_id": f.facility_id,
        "name": f.name,
        "location": f.location,
        "grid_region_code": f.grid_region_code,
    }

@router.put("/{facility_id}")
def update_facility(facility_id: int, payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    f = (
        db.query(Facility)
        .filter(Facility.facility_id == facility_id, Facility.org_id == user.org_id)
        .first()
    )
    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    f.name = payload.get("name") or f.name
    f.location = payload.get("location") or f.location
    f.grid_region_code = payload.get("grid_region_code") or f.grid_region_code
    db.commit()
    db.refresh(f)
    return {"ok": True}

# ---------- HTML PAGES ----------
pages = APIRouter(tags=["pages"])

@pages.get("/facilities", response_class=HTMLResponse)
def facilities_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("facilities_list.html", {"request": request})

@pages.get("/facilities/{facility_id}", response_class=HTMLResponse)
def facility_detail_page(facility_id: int, request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("facility_detail.html", {"request": request})