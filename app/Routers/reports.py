# app/Routers/reports.py
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from ..security import get_current_user

router = APIRouter(prefix="/api/reports", tags=["reports"])
pages = APIRouter(tags=["reports:pages"])

templates = Jinja2Templates(directory="app/templates")

# -------- PAGE ROUTES (HTML) --------
@pages.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("reports.html", {"request": request})

# -------- API ROUTES (JSON) --------
@router.get("/summary")
def reports_summary(scope: str | None = None, facility_id: int | None = None,
                    period: str = "monthly", user=Depends(get_current_user)):
    # TODO: replace with real aggregation of ActivityLog + EmissionFactor
    return {
        "scope": scope or "all",
        "facility_id": facility_id,
        "period": period,
        "series": [
            {"month": "2025-01", "kg_co2e": 12000},
            {"month": "2025-02", "kg_co2e": 9800},
            {"month": "2025-03", "kg_co2e": 11250},
        ],
        "total": 33050,
        "unit": "kg CO2e"
    }
