# app/Routers/factors.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
import csv
from io import StringIO
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

from fastapi import UploadFile, File
import csv
from io import StringIO

# ---------- Emission factors ----------

@router.get("/factors")
def list_factors(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # List all factors (you can later filter by source/year if you want)
    return (
        db.query(EmissionFactor)
        .order_by(EmissionFactor.category, EmissionFactor.unit, EmissionFactor.year.desc())
        .all()
    )


@router.post("/factors")
def create_factor(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    category = (payload.get("category") or payload.get("name") or "").strip()
    unit = (payload.get("unit") or "").strip()
    source = (payload.get("source") or "").strip()
    factor_raw = payload.get("factor") or payload.get("value")
    year_raw = payload.get("year")

    if not category or not unit or factor_raw in (None, ""):
        raise HTTPException(status_code=400, detail="Category, unit, and factor are required")

    try:
        factor_val = Decimal(str(factor_raw))
    except Exception:
        raise HTTPException(status_code=400, detail="Factor must be numeric")

    year_val = int(year_raw) if year_raw not in (None, "") else None

    ef = EmissionFactor(
        category=category,
        unit=unit,
        source=source or None,
        factor=factor_val,
        year=year_val,
    )
    db.add(ef)
    db.commit()
    db.refresh(ef)
    return ef


@router.post("/factors/import")
async def import_factors(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    content = (await file.read()).decode("utf-8", errors="ignore")
    reader = csv.DictReader(StringIO(content))

    count = 0
    for row in reader:
        category = (row.get("category") or row.get("name") or "").strip()
        if not category:
            continue

        unit = (row.get("unit") or "").strip()
        value_raw = (
            row.get("value_per_unit")
            or row.get("factor")
            or row.get("value")
            or ""
        )
        source = (row.get("source") or "").strip()
        year_raw = row.get("year")

        if not unit or value_raw == "":
            continue

        try:
            factor_val = Decimal(str(value_raw))
        except Exception:
            continue

        year_val = int(year_raw) if year_raw not in (None, "") else None

        ef = EmissionFactor(
            category=category,
            unit=unit,
            source=source or None,
            factor=factor_val,
            year=year_val,
        )
        db.add(ef)
        count += 1

    db.commit()
    return {"imported": count}
