# NirikshAi: AI-Assisted Institutional Compliance & Risk-Based Inspection Platform

> **Smart India Hackathon 2026** — Automated institutional monitoring, CCTV headcount discrepancy auditing, and explainable risk-based inspector dispatch.

---

## 📌 Executive Summary

Government vocational and skill development programs (e.g., Skill India, PMSSS, National Apprenticeship Promotion Scheme) often suffer from **attendance inflation and "ghost beneficiary" registration**. Training centers self-report inflated attendance to claim operational subsidies while physical classroom occupancy is substantially lower.

**NirikshAi** solves this accountability gap by creating an automated, cross-signal verification pipeline:
1. **Vision-Based Occupancy Telemetry**: Ingests classroom CCTV streams, running YOLOv8 person detection to compute true occupancy curves.
2. **Multi-Day Discrepancy Analysis**: Compares MIS-reported batch counts against verified headcounts over 7 days, filtering out single-day noise to identify systemic, persistent attendance gaps.
3. **Transparent 5-Factor Risk Scoring**: Computes an auditable risk score (0–100) weighting attendance gaps (30%), camera downtime (25%), past findings (20%), video-call failures (15%), and statutory compliance delays (10%).
4. **Smart Inspector Dispatch**: Directs physical surprise inspections with high-risk priority multipliers ($7\times$).
5. **Closed-Loop Feedback**: Field inspection findings submitted by mobile auditors dynamically recalibrate the institution's risk score and audit history in real-time.

---

## 🏛 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       NirikshAi UI                          │
│        (React 18 + TypeScript + Vite + Vanilla CSS)         │
│  - Real-Time KPI Telemetry       - Center Risk Inspector    │
│  - 7-Day Attendance Curves       - Closed-Loop Audit Dialog │
│  - CCTV Headcount Timeline       - DPDP Governance Modal    │
└──────────────┬──────────────────────────────▲───────────────┘
               │ HTTP Requests                │ WebSocket Updates
               ▼                              │
┌─────────────────────────────────────────────┴───────────────┐
│                    FastAPI Backend Core                     │
│  - API v1 Layer (/institutions, /inspections, /cctv, /stats)│
│  - ConnectionManager (WebSocket /ws/risk-updates)           │
│  - Domain Services:                                         │
│    • RiskEngine (5-Factor Weighted Scorer)                  │
│    • AttendanceAnalyzer (Pattern Discrepancy & Trends)      │
│    • CctvAnalyzer (YOLOv8 + Deterministic Mock Fallback)   │
└──────────────┬──────────────────────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Persistence Layer                        │
│  - SQLite (demo.db) + SQLAlchemy ORM 2.0                    │
│  - Zero-Infrastructure Portability for SIH Judging          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
NirikshAi/
├── backend/
│   ├── app/
│   │   ├── api/                   # Versioned REST endpoints (v1)
│   │   │   ├── deps.py            # FastAPI dependency injection (get_db)
│   │   │   └── v1/
│   │   │       ├── router.py      # Central v1 route aggregator
│   │   │       └── endpoints/     # Domain routers (institutions, inspections, cctv, stats)
│   │   ├── core/                  # Engine, session factory, settings
│   │   ├── models/                # SQLAlchemy ORM models (Institution, Attendance, Inspection)
│   │   ├── schemas/               # Strict Pydantic v2 schemas and request contracts
│   │   ├── services/              # Pure domain services (RiskEngine, Attendance, CCTV)
│   │   ├── websocket/             # Real-time WebSocket connection manager
│   │   └── main.py                # FastAPI application factory
│   ├── main.py                    # Root entrypoint wrapper (uvicorn main:app)
│   ├── seed.py                    # Standalone database seeder (10 centers across 3 risk tiers)
│   ├── test_smoke.py              # Automated test suite (live server & TestClient)
│   ├── requirements.txt           # Python dependencies
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── api/                   # Backend HTTP client & WebSocket subscriber
│   │   ├── components/            # UI components (Navbar, Stats, List, Detail, Chart, Modal, CCTV)
│   │   ├── styles/                # Design tokens & Apple-inspired CSS system
│   │   ├── types/                 # TypeScript interfaces matching backend models
│   │   ├── utils/                 # Formatters and presentation helpers
│   │   ├── App.tsx                # Main application coordinator
│   │   └── main.tsx               # React mount point
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── demo.db                        # Pre-seeded SQLite database ready for immediate demo
├── .gitignore
├── LICENSE
└── README.md
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Node.js 18+ and npm 9+

### 1. Backend Setup
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Seed the database (creates 10 institutions with 7-day attendance records)
python seed.py

# Launch development server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 2. Frontend Setup
In a new terminal:
```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

### 3. Automated Smoke Tests
Validate all endpoints and the closed-loop risk calculation:
```bash
cd backend
python test_smoke.py
```

---

## 📊 Evaluation & Judging Demo Script (5 Minutes)

1. **Minute 0–1: Dashboard Overview**
   - Review overall system metrics (Monitored Training Centers, Immediate Inspection Flags, System Average Risk Score).
   - Observe the risk-ranked centers directory (Navjeevan Skill Centre ranked at top with highest risk score).
2. **Minute 1–3: Discrepancy & Explainability**
   - Click **Navjeevan Skill Centre** to inspect the 7-day attendance discrepancy curve (reported 105 vs observed 45 headcount, 57.4% persistent gap).
   - Inspect the **Explainable Risk Drivers** breakdown detailing the exact contribution of each factor.
3. **Minute 3–4: Closed-Loop Inspection Audit**
   - Click **Conduct Inspection** to simulate a physical surprise audit.
   - Mark non-functional CCTV and unverified beneficiaries, then click **Confirm and Recalculate Risk**.
   - Notice the live update: the center's risk score increases immediately, and the new score is broadcast to connected clients via WebSocket.
4. **Minute 4–5: Vision Telemetry**
   - Switch to the **CCTV Verification** tab.
   - Click **Run Benchmark Telemetry** to view the second-by-second headcount timeline, peak occupancy, and frame counts.

---

## ⚖️ Governance & Compliance

NirikshAi adheres to the **Digital Personal Data Protection (DPDP) Act, 2023**:
- Surveillance streams are processed in-memory solely for headcount aggregation.
- Raw video frames and facial biometrics are never stored or indexed.
- Field audits generate immutable administrative logs with cryptographic timestamps.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
