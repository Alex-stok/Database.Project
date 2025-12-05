# app/Routers/forecast.py
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from decimal import Decimal
from ..database import get_db
from ..security import get_current_user
from ..models import ForecastScenario, ActivityLog, Facility

router = APIRouter(prefix="/api/forecast", tags=["forecast"])
pages = APIRouter(tags=["forecast:pages"])

@pages.get("/forecast", response_class=HTMLResponse)
def page(request: Request, user=Depends(get_current_user)):
    return request.app.state.templates.TemplateResponse("forecast.html", {"request": request})

def total_emissions_for_year(org_id: int, year: int, db: Session) -> Decimal:
    q = (
        db.query(ActivityLog)
        .join(Facility)
        .filter(Facility.org_id == org_id)
        .filter(ActivityLog.activity_date != None)
        .filter(ActivityLog.activity_date.between(f"{year}-01-01", f"{year}-12-31"))
    )
    total = Decimal("0")
    for r in q.all():
        total += Decimal(str(r.co2e_kg or 0))
    return total

@router.post("/scenario")
def create_scenario(payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    sc = ForecastScenario(
        org_id=user.org_id,
        name=payload["name"],
        description=payload.get("description"),
        annual_growth_pct=payload.get("annual_growth_pct"),
        renewable_share_pct=payload.get("renewable_share_pct"),
        start_year=payload["start_year"],
        end_year=payload["end_year"],
        created_by=user.user_id,
    )
    db.add(sc)
    db.commit()
    db.refresh(sc)
    return {"created": True, "scenario_id": sc.scenario_id}

@router.get("/scenario/{scenario_id}")
def scenario_results(scenario_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    sc = db.query(ForecastScenario).filter_by(scenario_id=scenario_id, org_id=user.org_id).first()
    if not sc:
        raise HTTPException(404, "Scenario not found")

    results = []
    current = total_emissions_for_year(user.org_id, sc.start_year, db)
    growth = Decimal(str(sc.annual_growth_pct or 0)) / Decimal("100")
    renewable = Decimal(str(sc.renewable_share_pct or 0)) / Decimal("100")

    for yr in range(sc.start_year, sc.end_year + 1):
        if yr > sc.start_year:
            current = current * (1 + growth)
        adjusted = current * (1 - renewable)

        results.append({
            "year": yr,
            "projected_kg": float(adjusted),
        })

    return {"scenario": sc.name, "results": results}
