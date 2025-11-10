# app/Routers/factors.py
from fastapi import APIRouter, Depends, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from ..security import get_current_user
from ..models import EmissionFactor

templates = Jinja2Templates(directory="app/templates")

# ---------- JSON API ----------
router = APIRouter(prefix="/api/factors", tags=["factors"])

@router.get("")
def list_factors(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.query(EmissionFactor).all()
    return [{"factor_id": r.factor_id, "source": r.source, "category": r.category, "unit": r.unit, "factor": float(r.factor), "year": r.year} for r in rows]

@router.post("/import")
async def import_factors(file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    # CSV parsing stub – put your import logic here
    content = await file.read()
    # parse content...
    return {"ok": True, "bytes": len(content)}

# ---------- HTML PAGES ----------
pages = APIRouter(tags=["pages"])

@pages.get("/factors", response_class=HTMLResponse)
def factors_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("factors_list.html", {"request": request})

@pages.get("/factors/import", response_class=HTMLResponse)
def factors_import_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("factors_import.html", {"request": request})
