def seed_defaults(db):
    from app.models import Unit, ActivityType

    units = [
        ("kWh", "Electricity kilowatt-hour"),
        ("therm", "Natural Gas"),
        ("gal", "Liquid fuel gallons"),
        ("m3", "Water cubic meters")
    ]

    for code, desc in units:
        if not db.query(Unit).filter_by(code=code).first():
            db.add(Unit(code=code, description=desc))

    types = [
        ("electricity", "Electricity", 2, "kWh"),
        ("natural_gas", "Natural Gas", 1, "therm"),
        ("diesel", "Diesel Fuel", 1, "gal"),
        ("water", "Water Usage", 3, "m3"),
    ]

    for code, label, scope, unit_code in types:
        default_unit = db.query(Unit).filter_by(code=unit_code).first()
        if not db.query(ActivityType).filter_by(code=code).first():
            db.add(ActivityType(code=code, label=label, scope=scope, default_unit_id=default_unit.unit_id))

    db.commit()
