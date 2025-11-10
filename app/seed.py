# app/seed.py
from sqlalchemy.orm import Session
from .models import EmissionFactor, Unit, ActivityType

# NOTE: These numbers are conservative placeholders so the app works end-to-end.
# Replace with official values when you import EPA eGRID / DEFRA CSVs later.

# Strategy since we are NOT changing schema:
# - Keep region specificity in the *source* label (e.g., "eGRID 2022 CAMX").
# - Keep category the same ("Electricity") and unit as "kgCO2e/kWh".
# - Your resolver can pick by matching source that contains the facility's grid_region_code,
#   otherwise fall back to a US average entry.

STARTER_FACTORS = [
    # Electricity (kgCO2e/kWh)
    {"source": "eGRID 2022 US_AVG", "category": "Electricity", "unit": "kgCO2e/kWh", "factor": 0.40, "year": 2022},
    {"source": "eGRID 2022 CAMX",   "category": "Electricity", "unit": "kgCO2e/kWh", "factor": 0.23, "year": 2022},
    {"source": "eGRID 2022 RFCW",   "category": "Electricity", "unit": "kgCO2e/kWh", "factor": 0.48, "year": 2022},
    {"source": "eGRID 2022 SRSO",   "category": "Electricity", "unit": "kgCO2e/kWh", "factor": 0.55, "year": 2022},
    {"source": "eGRID 2022 NWPP",   "category": "Electricity", "unit": "kgCO2e/kWh", "factor": 0.35, "year": 2022},
    {"source": "eGRID 2022 RMPA",   "category": "Electricity", "unit": "kgCO2e/kWh", "factor": 0.53, "year": 2022},

    # Scope 1 common fuels (US units)
    {"source": "DEFRA 2023 (starter)", "category": "Diesel",     "unit": "kgCO2e/gal",   "factor": 10.2, "year": 2023},
    {"source": "DEFRA 2023 (starter)", "category": "Gasoline",   "unit": "kgCO2e/gal",   "factor": 8.9,  "year": 2023},
    {"source": "DEFRA 2023 (starter)", "category": "NaturalGas", "unit": "kgCO2e/therm", "factor": 5.3,  "year": 2023},

    # Simple freight example (Scope 3)
    {"source": "GLEC 2023 (starter)",  "category": "Freight_Truck", "unit": "kgCO2e/ton-mile", "factor": 0.16, "year": 2023},
]

def _ensure_factor(db: Session, row: dict) -> None:
    exists = (
        db.query(EmissionFactor)
          .filter(
              EmissionFactor.source == row["source"],
              EmissionFactor.category == row["category"],
              EmissionFactor.unit == row["unit"],
              EmissionFactor.year == row["year"],
          )
          .first()
    )
    if not exists:
        db.add(EmissionFactor(
            source=row["source"],
            category=row["category"],
            unit=row["unit"],
            factor=row["factor"],
            year=row["year"],
        ))

def seed_emission_factors(db: Session) -> None:
    """Idempotent: insert only if (source, category, unit, year) combo is missing."""
    for row in STARTER_FACTORS:
        _ensure_factor(db, row)
    db.commit()

def seed_all(db: Session) -> None:
    """Called once on startup."""
    seed_emission_factors(db)
    seed_units(db)
    seed_activity_types(db)

def seed_units(db):
    units = [
        {"code": "kWh", "description": "Kilowatt-hour"},
        {"code": "therm", "description": "Therm (natural gas)"},
        {"code": "gal", "description": "US gallon"},
        {"code": "L", "description": "Liter"},
        {"code": "kg", "description": "Kilogram"},
        {"code": "ton-mile", "description": "Ton-mile of freight"},
        {"code": "km", "description": "Kilometer"},
        {"code": "mi", "description": "Mile"},
        {"code": "kgCO2e", "description": "Kilogram CO₂ equivalent"},
        {"code": "MWh", "description": "Megawatt-hour"},
    ]
    for row in units:
        if not db.query(Unit).filter_by(code=row["code"]).first():
            db.add(Unit(**row))
    db.commit()

def seed_activity_types(db):
    unit_lookup = {u.code: u.unit_id for u in db.query(Unit).all()}
    types = [
        {"code": "ELEC_USE", "label": "Electricity Use", "scope": "2", "default_unit_id": unit_lookup.get("kWh")},
        {"code": "NAT_GAS", "label": "Natural Gas", "scope": "1", "default_unit_id": unit_lookup.get("therm")},
        {"code": "DIESEL", "label": "Diesel Fuel", "scope": "1", "default_unit_id": unit_lookup.get("gal")},
        {"code": "GASOLINE", "label": "Gasoline Fuel", "scope": "1", "default_unit_id": unit_lookup.get("gal")},
        {"code": "AIR_TRAVEL", "label": "Air Travel (Commercial)", "scope": "3", "default_unit_id": unit_lookup.get("km")},
        {"code": "FREIGHT_TRUCK", "label": "Freight Transport (Truck)", "scope": "3", "default_unit_id": unit_lookup.get("ton-mile")},
        {"code": "FREIGHT_SHIP", "label": "Freight Transport (Ship)", "scope": "3", "default_unit_id": unit_lookup.get("ton-mile")},
        {"code": "WASTE", "label": "Waste Disposal", "scope": "3", "default_unit_id": unit_lookup.get("kg")},
        {"code": "WATER", "label": "Water Usage", "scope": "3", "default_unit_id": unit_lookup.get("L")},
    ]
    for row in types:
        if not db.query(ActivityType).filter_by(code=row["code"]).first():
            db.add(ActivityType(**row))
    db.commit()
