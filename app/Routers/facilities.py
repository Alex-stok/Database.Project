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

@router.get("", summary="List facilities")
@router.get("/", include_in_schema=False)
def list_facilities(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = (
        db.query(Facility)
        .filter(Facility.org_id == user.org_id)
        .all()
    )
    return [
        {
            "facility_id": f.facility_id,
            "name": f.name,
            "location": f.location,
            "grid_region_code": f.grid_region_code,
        } for f in rows
    ]

@router.post("", summary="Create facility")
@router.post("/", include_in_schema=False)
def create_facility(payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    f = Facility(
        org_id=user.org_id,
        name=payload.get("name"),
        location=payload.get("location"),
        grid_region_code=payload.get("grid_region_code"),
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return {"facility_id": f.facility_id}

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