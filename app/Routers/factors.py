# app/Routers/factors.py

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import csv
from decimal import Decimal

from ..database import get_db
from ..security import get_current_user
from ..models import EmissionFactor

router = APIRouter(prefix="/api/factors", tags=["factors"])


# ------------------------------------------------------------
# GET list factors
# ------------------------------------------------------------
@router.get("")
def list_factors(db: Session = Depends(get_db)):
    rows = db.query(EmissionFactor).order_by(
        EmissionFactor.category, EmissionFactor.year.desc()
    ).all()

    return [
        {
            "factor_id": f.factor_id,
            "source": f.source,
            "category": f.category,
            "unit": f.unit,
            "factor": float(f.factor),
            "year": f.year,
        }
        for f in rows
    ]


# ------------------------------------------------------------
# POST create factor manually
# ------------------------------------------------------------
@router.post("")
def create_factor(payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):

    try:
        factor_val = Decimal(str(payload.get("factor")))
    except:
        raise HTTPException(400, "factor must be numeric")

    ef = EmissionFactor(
        source=payload.get("source") or "manual",
        category=payload.get("category"),
        unit=payload.get("unit"),
        factor=factor_val,
        year=payload.get("year") or None,
    )
    db.add(ef)
    db.commit()
    db.refresh(ef)

    return {"factor_id": ef.factor_id}


# ------------------------------------------------------------
# POST /api/factors/import
# CSV columns expected: source,category,unit,factor,year
# ------------------------------------------------------------
@router.post("/import")
def import_factors(file: UploadFile = File(...),
                   db: Session = Depends(get_db),
                   user=Depends(get_current_user)):

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Must upload CSV")

    content = file.file.read().decode("utf-8").splitlines()
    reader = csv.DictReader(content)

    imported = 0

    for row in reader:
        try:
            val = Decimal(row["factor"])
        except:
            continue

        ef = EmissionFactor(
            source=row.get("source") or "CSV",
            category=row.get("category"),
            unit=row.get("unit"),
            factor=val,
            year=int(row["year"]) if row.get("year") else None,
        )
        db.add(ef)
        imported += 1

    db.commit()

    return {"imported": imported}
