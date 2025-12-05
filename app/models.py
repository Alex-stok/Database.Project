# app/models.py
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Date, Numeric, Text,
    DECIMAL, JSON, TIMESTAMP
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# -------------------------
# Core
# -------------------------
class Organization(Base):
    __tablename__ = "organization"
    org_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    industry = Column(String(128))
    address = Column(Text)
    size = Column(String(64))  # e.g., "1-50", "51-200"

    users = relationship("User", back_populates="organization", cascade="all,delete")
    facilities = relationship("Facility", back_populates="organization", cascade="all,delete")
    targets = relationship("Target", back_populates="organization", cascade="all,delete-orphan")
    scenarios = relationship("ForecastScenario", back_populates="organization", cascade="all,delete-orphan")
    org_actions = relationship("OrgAction", back_populates="organization", cascade="all,delete-orphan")
    uploads = relationship("UploadedFile", back_populates="organization", cascade="all,delete-orphan")


class User(Base):
    __tablename__ = "user"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(64), default="member")
    org_id = Column(Integer, ForeignKey("organization.org_id"))

    organization = relationship("Organization", back_populates="users")
    created_targets = relationship("Target", back_populates="creator")
    created_scenarios = relationship("ForecastScenario", back_populates="creator")
    uploads = relationship("UploadedFile", back_populates="uploader")


class Facility(Base):
    __tablename__ = "facility"
    facility_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organization.org_id"), nullable=False)
    name = Column(String(255))
    location = Column(Text)
    grid_region_code = Column(String(64))

    organization = relationship("Organization", back_populates="facilities")
    activities = relationship("ActivityLog", back_populates="facility", cascade="all,delete-orphan")
    org_actions = relationship("OrgAction", back_populates="facility")


class EmissionFactor(Base):
    __tablename__ = "emission_factor"
    factor_id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(128))                # e.g., DEFRA, EPA eGRID
    category = Column(String(128))              # e.g., Electricity, Diesel
    unit = Column(String(64))                   # e.g., kgCO2e/kWh
    factor = Column(Numeric(14, 6))             # numeric value
    year = Column(Integer)

    activities = relationship("ActivityLog", back_populates="factor")


# -------------------------
# New lookups (for forms)
# -------------------------
class Unit(Base):
    __tablename__ = "unit"
    unit_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), nullable=False, unique=True)      # 'kWh','therm','gal','kg', ...
    description = Column(String(255))

    activities = relationship("ActivityLog", back_populates="unit_fk")


class ActivityType(Base):
    __tablename__ = "activity_type"
    activity_type_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), nullable=False, unique=True)      # 'electricity','diesel','shipping', ...
    label = Column(String(128), nullable=False)
    scope = Column(Integer)                                     # 1, 2 or 3
    default_unit_id = Column(Integer, ForeignKey("unit.unit_id"))

    default_unit = relationship("Unit")
    activities = relationship("ActivityLog", back_populates="activity_type_fk")


# -------------------------------------
# Activity log (adds optional FKs/cols)
# -------------------------------------
class ActivityLog(Base):
    __tablename__ = "activity_log"
    activity_id = Column(Integer, primary_key=True, autoincrement=True)

    facility_id = Column(Integer, ForeignKey("facility.facility_id"), nullable=False)
    factor_id   = Column(Integer, ForeignKey("emission_factor.factor_id"), nullable=False)

    # Original flexible fields (kept for compatibility)
    activity_type = Column(String(128))          # free-text legacy
    quantity      = Column(Numeric(14, 6))
    unit          = Column(String(64))           # free-text legacy
    activity_date = Column(Date)

    # New, structured fields (nullable so old rows still work)
    activity_type_id = Column(Integer, ForeignKey("activity_type.activity_type_id"), nullable=True)
    unit_id          = Column(Integer, ForeignKey("unit.unit_id"), nullable=True)

    notes   = Column(String(512))
    co2e_kg = Column(Numeric(18, 6))             # store computed CO2e for fast reporting

    facility = relationship("Facility", back_populates="activities")
    factor   = relationship("EmissionFactor", back_populates="activities")
    activity_type_fk = relationship("ActivityType", back_populates="activities")
    unit_fk         = relationship("Unit", back_populates="activities")


# -------------------------
# Targets & forecasting
# -------------------------
class Target(Base):
    __tablename__ = "target"
    target_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organization.org_id"), nullable=False)
    baseline_year = Column(Integer, nullable=False)
    baseline_co2e_kg = Column(Numeric(18, 6))
    target_year = Column(Integer, nullable=False)
    reduction_percent = Column(Numeric(5, 2), nullable=False)  # e.g., 30.00

    created_by = Column(Integer, ForeignKey("user.user_id"))
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    organization = relationship("Organization", back_populates="targets")
    creator = relationship("User", back_populates="created_targets")


class ForecastScenario(Base):
    __tablename__ = "forecast_scenario"
    scenario_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organization.org_id"), nullable=False)

    name = Column(String(128), nullable=False)
    description = Column(String(512))

    annual_growth_pct = Column(Numeric(6, 3))    # % growth in activity demand
    renewable_share_pct = Column(Numeric(6, 3))  # % of electricity from renewables

    start_year = Column(Integer, nullable=False)
    end_year   = Column(Integer, nullable=False)

    created_by = Column(Integer, ForeignKey("user.user_id"))
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    organization = relationship("Organization", back_populates="scenarios")
    creator = relationship("User", back_populates="created_scenarios")


# -------------------------
# Planner (actions)
# -------------------------
class ActionLibrary(Base):
    __tablename__ = "action_library"
    action_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), nullable=False, unique=True)
    name = Column(String(128), nullable=False)
    description = Column(String(512))
    expected_reduction_pct = Column(Numeric(6, 3))
    default_capex_usd = Column(Numeric(18, 2))
    default_life_years = Column(Numeric(6, 2))

    org_actions = relationship("OrgAction", back_populates="action")


class OrgAction(Base):
    __tablename__ = "org_action"
    org_action_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organization.org_id"), nullable=False)
    action_id = Column(Integer, ForeignKey("action_library.action_id"), nullable=False)
    facility_id = Column(Integer, ForeignKey("facility.facility_id"))

    custom_params = Column(JSON)                  # free-form knobs (e.g., {"fleet_pct":25})
    est_reduction_kg = Column(Numeric(18, 6))
    est_capex_usd = Column(Numeric(18, 2))
    planned_year = Column(Integer)
    status = Column(String(24))                   # planned | in_progress | done

    organization = relationship("Organization", back_populates="org_actions")
    action = relationship("ActionLibrary", back_populates="org_actions")
    facility = relationship("Facility", back_populates="org_actions")


# -------------------------
# File uploads (CSV, etc.)
# -------------------------
class UploadedFile(Base):
    __tablename__ = "uploaded_file"
    file_id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organization.org_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.user_id"))
    purpose = Column(String(32), nullable=False)       # 'energy','fuel','shipping','factors','other'
    storage_path = Column(String(512), nullable=False)
    original_name = Column(String(255), nullable=False)
    content_type = Column(String(128))
    uploaded_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    organization = relationship("Organization", back_populates="uploads")
    uploader = relationship("User", back_populates="uploads")
