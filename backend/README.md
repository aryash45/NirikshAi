# NirikshAi Backend

Enterprise-grade, modular FastAPI backend for AI-assisted institutional monitoring, risk-based inspection targeting, and real-time verification.

---

## 🏛 Architecture Overview

```
backend/
├── app/
│   ├── __init__.py                # Package initialization, exports `app`
│   ├── main.py                    # FastAPI instance creation, lifespan, CORS, middleware, router mount
│   ├── core/
│   │   ├── __init__.py            # Re-exports settings, engine, Base
│   │   ├── config.py              # Application settings (env vars, project name, API prefixes, CORS origins)
│   │   └── database.py            # SQLite engine, SessionLocal, declarative Base, get_db dependency
│   ├── models/
│   │   ├── __init__.py            # Re-exports Base, Institution, AttendanceRecord, Inspection
│   │   ├── institution.py         # Institution ORM model
│   │   ├── attendance.py          # AttendanceRecord ORM model
│   │   └── inspection.py          # Inspection ORM model
│   ├── schemas/
│   │   ├── __init__.py            # Central schema registry exporting all DTOs/contracts
│   │   ├── common.py              # Common models / enums / stats summary
│   │   ├── attendance.py          # AttendanceSeries, AttendancePatternResult
│   │   ├── risk.py                # RiskDrivers breakdown schema
│   │   ├── institution.py         # InstitutionBase, InstitutionSummary, InstitutionDetail
│   │   ├── inspection.py          # InspectionFindings, InspectionCreate, InspectionOut, InspectionResponse
│   │   └── cctv.py                # OccupancyPoint, CctvAnalysisResult
│   ├── services/
│   │   ├── __init__.py            # Re-exports domain services
│   │   ├── risk_engine.py         # 5-factor weighted risk engine with explainable drivers
│   │   ├── attendance_analyzer.py # Multi-day attendance anomaly detection & trend analysis
│   │   └── cctv_analyzer.py       # YOLOv8 person detector with deterministic mock fallback
│   ├── api/
│   │   ├── __init__.py            # Re-exports api_router
│   │   ├── deps.py                # Common FastAPI dependencies (e.g. get_db)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py          # Central v1 router mounting sub-routers
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── institutions.py# /institutions endpoints
│   │           ├── inspections.py # /inspections endpoints (closed loop feedback)
│   │           ├── cctv.py        # /cctv endpoints (video + mock)
│   │           └── stats.py       # /stats/summary endpoint
│   └── websocket/
│       ├── __init__.py
│       └── manager.py             # ConnectionManager for real-time WebSocket broadcast
├── main.py                        # Root convenience entrypoint wrapper
├── seed.py                        # Standalone database seeder script
├── test_smoke.py                  # Integration smoke test suite
└── requirements.txt               # Dependencies
```

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Seed Database
Seeds 10 institutions (High, Medium, and Low risk tiers) with 7 days of attendance records:
```bash
python seed.py
```

### 3. Start Development Server
You can launch the server using either:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
or via the root wrapper:
```bash
python main.py
```

### 4. Interactive Documentation
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Verification & Testing
Run the automated smoke test suite:
```bash
python test_smoke.py
```
This tests all health, institution listing, detail with attendance analysis, closed-loop inspection feedback with live risk recalculation, and CCTV mock endpoints.
