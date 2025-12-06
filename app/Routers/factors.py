# app/Routers/factors.py
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import get_current_user
from ..models import EmissionFactor
from ..schemas import FactorOut

router = APIRouter(prefix="/api/factors", tags=["factors"])
pages = APIRouter(tags=["factors:pages"])


@pages.get("/factors", response_class=HTMLResponse)
def factors_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "factors_list.html",
        {"request": request},
    )


@router.get("", response_model=list[FactorOut])
def list_factors(db: Session = Depends(get_db), user=Depends(get_current_user)):
    # In this version we just return all factors.
    # If you want org-specific later, you can filter by user.org_id.
    return db.query(EmissionFactor).all()


@router.post("")
def create_factor(payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    f = EmissionFactor(
        source=payload.get("source"),
        category=payload["category"],
        unit=payload["unit"],
        factor=payload["factor"],
        year=payload.get("year"),
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return {"created": True, "factor_id": f.factor_id}
