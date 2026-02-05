# Sustainability Tracking and Emissions Management System

**Project Report**  
**Course:** CSC 4710  
**Author:** Alex Stokes

---

## 1. Introduction

### 1.1 Project Overview

This project implements a **Sustainability Tracking and Emissions Management System**, a full-stack web application enabling organizations to:

- Log energy and fuel usage  
- Compute carbon emissions  
- Store and manage emission factors  
- Forecast future emissions  
- Plan reduction strategies  
- Generate reports  
- Manage users and organizations  

The system includes:

- A FastAPI backend with structured REST APIs  
- A MySQL database containing normalized, interrelated entities  
- A Jinja2 + JavaScript front end with modern UI and dynamic fetch calls  
- Secure JWT-based authentication  
- Modules for facilities, activities, factors, files, targets, forecasting, planning, and reporting  

---

### 1.2 Motivation

GHG (Greenhouse Gas) tracking and sustainability analytics have become mandatory for organizations targeting ESG compliance and emissions reduction. Industry-grade tools are often inaccessible or costly.

This project addresses the need for a functional, end-to-end emissions management system while satisfying core database-systems requirements:

- Normalization
- CRUD operations
- Multi-table queries
- Aggregate functions
- Complete UI interaction

The application demonstrates real-world domain depth and complex database interactions suitable for an academic database systems course.

---

### 1.3 Key System Components

- **Database Layer:** SQLAlchemy ORM models for all sustainability entities  
- **API Layer:** Facilities, factors, reports, uploads, targets, forecast, planner, and authentication  
- **Web Layer:** Dashboard, list pages, detail pages, AJAX update forms  
- **Security Layer:** Password hashing and JWT validation  

---

## 2. Database Details

### 2.1 Database Design Strategy

The schema is designed around central sustainability accounting concepts:

- Organizations, users, and permissions  
- Facilities and grid regions  
- Emission factors mapped to activities  
- Targets, forecasting, and planning entities  

When a new activity is inserted:

- `ActivityType` and `Unit` are selected via seeded dropdowns  
- The appropriate `EmissionFactor` is automatically resolved  
- The most recent applicable factor is selected  
- CO₂e is computed before committing the `ActivityLog` row  

The updated schema introduces seeded lookup tables (`Unit`, `ActivityType`) to ensure:

- Consistent unit handling  
- Activity classification by Scope (1, 2, or 3)  
- Reduced redundancy  

CO₂e emissions are computed during activity creation and stored directly in  
`ActivityLog.co2e_kg`, reducing reporting-time computation.

This relational model supports extensibility, normalization, and separation of concerns.

---

### 2.2 ER Model Summary

Key relationships:

- Organization → Users (1:N)  
- Organization → Facilities (1:N)  
- Facility → ActivityLog (1:N)  
- EmissionFactor → ActivityLog (1:N)  
- User → Targets / ForecastScenarios (1:N)  
- Organization → UploadedFiles / OrgActions (1:N)  
- ActionLibrary → OrgAction (1:N)  
- ActivityType → ActivityLog (1:N)  
- Unit → ActivityLog (1:N)  

---

### 2.3 Relational Schema Overview

Representative tables (full definitions in the source code):

- Organization(org_id, name, industry, address, size)  
- User(user_id, email, password_hash, full_name, role, org_id)  
- Facility(facility_id, org_id, name, location, grid_region_code)  
- EmissionFactor(factor_id, source, category, unit, factor, year)  
- ActivityLog(activity_id, facility_id, factor_id, activity_type_id, unit_id, quantity, activity_date, co2e_kg, notes)  
- Target(target_id, org_id, baseline_year, baseline_co2e_kg, target_year, reduction_percent, created_by)  
- ForecastScenario(scenario_id, org_id, name, annual_growth_pct, renewable_share_pct, start_year, end_year)  
- ActionLibrary(action_id, code, name, expected_reduction_pct, default_capex_usd)  
- OrgAction(org_action_id, org_id, action_id, facility_id, est_reduction_kg, status, …)  
- UploadedFile(file_id, org_id, user_id, purpose, storage_path, original_name, content_type, uploaded_at)  
- Unit(unit_id, code, description)  
- ActivityType(activity_type_id, code, label, scope, default_unit_id)  

---

### 2.4 Normalization and Functional Dependencies

Examples:

- email → password_hash, role, full_name  
- (category, year) → factor, unit, source  
- facility_id → name, location, grid_region_code  

All tables satisfy **3NF or BCNF**:

- Every non-key attribute depends wholly on the primary key  
- No transitive dependencies  
- Lookup tables isolate repeating values  

---

### 2.5 Constraints

- Unique email enforcement  
- Numeric precision enforcement  
- Foreign-key linking between dependent entities  
- Cascading deletes for organization-owned resources  
- Activity creation and deletion enforce organization ownership  
- File uploads enforce organization ownership and physical file handling  
- Authentication accepts JWT tokens from cookies and Authorization headers  

---

## 3. Functionality Details

### 3.1 Core Database Functions

#### (1) Insert Records

- User registration (`/api/auth/register`)  
- Facility creation (`/api/facilities`)  
- Emission factor insertion and CSV import  
- File uploads (`/api/files/upload`)  

#### (2) Search and List Records

- Facilities list  
- Emission factor browser  
- Uploaded files list  
- User and organization profile display  

#### (3) Advanced Queries (Joins and Aggregates)

- Reporting engine aggregates CO₂e using `SUM(ActivityLog.co2e_kg)`  
- Forecast engine applies growth and renewable adoption over time  
- Reduction planner evaluates weighted reduction scenarios  

#### (4) Update Records

- Facility updates  
- User and organization profile updates  

#### (5) Delete Records

- Facility deletion  
- Uploaded file deletion  

---

### 3.2 Additional Features

- JWT-secured endpoints  
- Forecasting and action planning modules  

---

## 4. Implementation Details

### 4.1 Languages and Frameworks

- Python 3, FastAPI  
- MySQL  
- SQLAlchemy ORM  
- HTML, JavaScript, CSS  
- Jinja2 templating  
- JWT and bcrypt security  

---

### 4.2 Backend Architecture

Key files:

- `main.py` – Route registration and static mounting  
- `database.py` – Database engine and session creation  
- `models.py` – Complete relational schema  
- `security.py` – Authentication and password hashing  
- `schemas.py` – Pydantic validation  

---

### 4.3 Front-End Architecture

All UI pages reside in `/app/templates` and use JavaScript fetch calls for asynchronous CRUD operations.

---

## 5. Experiences and Reflections

### 5.1 Challenges

- Schema normalization  
- Secure authentication  
- Front-end and back-end synchronization  
- File uploads  
- Forecasting and planning logic  

### 5.2 What Was Learned

- End-to-end full-stack development  
- Real-world schema modeling  
- Advanced query design  
- API security patterns  
- Dynamic UI construction  

---

### 5.3 Future Work

Future enhancements include:

- Real-time CO₂e computation  
- Interactive visualization dashboards  
- Improved bulk data ingestion  
- Role-based access control  
- Automated emission-factor updates via external APIs  

---

## 6. Conclusion

This project demonstrates a fully functional sustainability tracking and emissions management platform. Through a normalized database schema, robust API layer, and intuitive web interface, the system fulfills all required database operations while modeling real-world environmental accounting workflows. The application provides a strong foundation for future analytical and automation-focused enhancements.



6. Conclusion
This project demonstrates the design and implementation of a fully functional sustainability tracking and emissions management platform. Through a normalized relational database schema, robust API layer, and intuitive front-end interface, the system supports all required core operations, including inserting, querying, updating, and deleting records, as well as executing advanced aggregate and join queries for reporting, forecasting, and planning. The application also incorporates secure authentication, file handling, and multi-entity interactions that mirror real-world environmental accounting workflows. Overall, the project achieves its intended purpose by combining solid database principles with practical full-stack development, providing a strong foundation for further enhancements and offering a realistic model of how organizations can monitor and manage their greenhouse gas emissions.
