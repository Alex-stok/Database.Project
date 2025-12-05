# app/Routers/facilities.py
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..security import get_current_user
from ..models import Facility

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/api/facilities", tags=["facilities"])
pages = APIRouter(tags=["pages"])

# ---------- CREATE FACILITY ----------
@router.post("")
def create_facility(payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    name = (payload.get("name") or "").strip()
    location = (payload.get("location") or "").strip()
    grid = (payload.get("grid_region_code") or "").strip()

    if not name:
        raise HTTPException(400, "Name required")

    fac = Facility(
        org_id=user.org_id,
        name=name,
        location=location or None,
        grid_region_code=grid or None
    )
    db.add(fac)
    db.commit()
    db.refresh(fac)
    return fac

# ---------- LIST FACILITIES ----------
@router.get("")
def list_facilities(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return (
        db.query(Facility)
        .filter(Facility.org_id == user.org_id)
        .order_by(Facility.facility_id)
        .all()
    )

# ---------- GET ONE FACILITY ----------
@router.get("/{facility_id}")
def get_facility(facility_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    fac = (
        db.query(Facility)
        .filter(Facility.facility_id == facility_id, Facility.org_id == user.org_id)
        .first()
    )
    if not fac:
        raise HTTPException(status_code=404, detail="Facility not found")

    return {
        "facility_id": fac.facility_id,
        "name": fac.name,
        "location": fac.location,
        "grid_region_code": fac.grid_region_code
    }

# ---------- UPDATE ----------
@router.put("/{facility_id}")
def update_facility(facility_id: int, payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    fac = (
        db.query(Facility)
        .filter(Facility.facility_id == facility_id, Facility.org_id == user.org_id)
        .first()
    )
    if not fac:
        raise HTTPException(404, "Facility not found")

    fac.name = payload.get("name") or fac.name
    fac.location = payload.get("location") or fac.location
    fac.grid_region_code = payload.get("grid_region_code") or fac.grid_region_code
    db.commit()
    db.refresh(fac)
    return {"ok": True}

# ---------- DELETE ----------
@router.delete("/{facility_id}")
def delete_facility(facility_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    fac = (
        db.query(Facility)
        .filter(Facility.facility_id == facility_id, Facility.org_id == user.org_id)
        .first()
    )
    if not fac:
        raise HTTPException(404, "Facility not found")

    db.delete(fac)
    db.commit()
    return {"deleted": True}

# ---------- HTML ----------
@pages.get("/facilities", response_class=HTMLResponse)
def facilities_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("facilities_list.html", {"request": request})

@pages.get("/facilities/{facility_id}", response_class=HTMLResponse)
def facility_detail_page(facility_id: int, request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("facility_detail.html", {"request": request, "facility_id": facility_id})
