# app/Routers/factors.py
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..security import get_current_user
from ..models import EmissionFactor

router = APIRouter(prefix="/api/factors", tags=["factors"])
pages = APIRouter(tags=["factors:pages"])

@pages.get("/factors", response_class=HTMLResponse)
def factors_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "factors_list.html",  
        {"request": request},
    )
@router.get("")
def get_factors(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(EmissionFactor).all()

@router.post("")
def create_factor(payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    f = EmissionFactor(
        source=payload["source"],
        category=payload["category"],
        unit=payload["unit"],
        factor=payload["factor"],
        year=payload.get("year")
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return {"created": True, "factor": f.factor_id}
