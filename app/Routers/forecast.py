# app/Routers/forecast.py
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from ..security import get_current_user

router = APIRouter(prefix="/api/forecast", tags=["forecast"])
pages = APIRouter(tags=["forecast:pages"])

templates = Jinja2Templates(directory="app/templates")

# -------- PAGE ROUTES (HTML) --------
@pages.get("/forecast", response_class=HTMLResponse)
def forecast_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("forecast.html", {"request": request})

# -------- API ROUTES (JSON) --------
@router.post("/run")
def run_forecast(params: dict, user=Depends(get_current_user)):
    # expected keys (placeholders): growth_pct, renewable_share_pct, years
    growth = float(params.get("growth_pct", 0))
    renewable = float(params.get("renewable_share_pct", 0))
    years = int(params.get("years", 3))

    base = 12000.0  # TODO: derive from recent average emissions
    out = []
    current = base
    for i in range(1, years + 1):
        current *= (1 + growth / 100.0)
        reduction = current * (renewable / 100.0) * 0.8  # fake “impact factor” placeholder
        projected = max(current - reduction, 0)
        out.append({"year_offset": i, "projected_kg_co2e": round(projected, 2)})

    return {"baseline_kg_co2e": base, "scenarios": out, "unit": "kg CO2e"}
