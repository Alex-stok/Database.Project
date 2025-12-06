# app/Routers/factors.py
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import get_current_user
from ..models import EmissionFactor
from ..schemas import FactorOut   # <-- import the schema

router = APIRouter(prefix="/api/factors", tags=["factors"])
pages = APIRouter(tags=["factors:pages"])


@pages.get("/factors", response_class=HTMLResponse)
def factors_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "factors_list.html",
        {"request": request},
    )


# Single JSON list endpoint for the front-end table
@router.get("", response_model=list[FactorOut])
def list_factors(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    rows = db.query(EmissionFactor).all()
    return rows


@router.post("", response_model=FactorOut)
def create_factor(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    f = EmissionFactor(
        source=payload["source"],
        category=payload["category"],
        unit=payload["unit"],
        factor=payload["factor"],
        year=payload.get("year"),
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f
