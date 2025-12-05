# app/Routers/planner.py
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from decimal import Decimal
from ..database import get_db
from ..security import get_current_user
from ..models import ActionLibrary, OrgAction, Facility

router = APIRouter(prefix="/api/planner", tags=["planner"])
pages = APIRouter(tags=["planner:pages"])

@pages.get("/planner", response_class=HTMLResponse)
def planner_page(request: Request, user=Depends(get_current_user)):
    return request.app.state.templates.TemplateResponse("planner.html", {"request": request})

@router.get("/library")
def get_library(db: Session = Depends(get_db)):
    return db.query(ActionLibrary).all()

@router.post("/library")
def add_action(payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    a = ActionLibrary(
        code=payload["code"],
        name=payload["name"],
        description=payload.get("description"),
        expected_reduction_pct=payload.get("expected_reduction_pct"),
        default_capex_usd=payload.get("default_capex_usd"),
        default_life_years=payload.get("default_life_years"),
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return {"created": True, "id": a.action_id}

@router.post("/apply")
def apply_action(payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    fac_id = payload.get("facility_id")

    if fac_id:
        fac = db.query(Facility).filter(Facility.facility_id == fac_id, Facility.org_id == user.org_id).first()
        if not fac:
            raise HTTPException(403, "Invalid facility")

    red_pct = Decimal(str(payload["estimated_reduction_pct"])) / Decimal("100")
    capex = Decimal(str(payload.get("capex_usd", 0)))

    act = OrgAction(
        org_id=user.org_id,
        action_id=payload["action_id"],
        facility_id=fac_id,
        est_reduction_kg=payload.get("est_reduction_kg"),
        est_capex_usd=capex,
        planned_year=payload.get("planned_year"),
        status="planned",
    )
    db.add(act)
    db.commit()
    return {"applied": True}
