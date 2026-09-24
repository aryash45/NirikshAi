"""
seed.py — Populates demo.db with 10 institutions and realistic attendance data.
Run once: python seed.py
Safe to re-run: drops and recreates tables.
"""

from __future__ import annotations
import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta
from app.core.database import engine, SessionLocal
from app.models import Base, Institution, AttendanceRecord, Inspection

# ── Institution seed data ──────────────────────────────────────────────────
INSTITUTIONS = [
    # HIGH RISK
    {
        "name": "Navjeevan Skill Centre",
        "scheme": "Skill India", "district": "Lucknow", "state": "Uttar Pradesh",
        "attendance_gap_pct": 57, "camera_uptime_pct": 82,
        "past_findings": 3, "vc_failures": 2, "compliance_days_overdue": 45,
        "reported": [105, 108, 102, 110, 103, 107, 104],
        "observed":  [45,  42,  48,  44,  46,  43,  47],
        "last_inspected": date(2025, 6, 10),
    },
    {
        "name": "Sahyadri Vocational Institute",
        "scheme": "Skill India", "district": "Nashik", "state": "Maharashtra",
        "attendance_gap_pct": 48, "camera_uptime_pct": 78,
        "past_findings": 2, "vc_failures": 2, "compliance_days_overdue": 38,
        "reported": [92, 95, 88, 98, 90, 93, 89],
        "observed":  [48, 50, 45, 52, 47, 49, 46],
        "last_inspected": date(2025, 5, 20),
    },
    {
        "name": "Ganga Technical Training",
        "scheme": "PMSSS", "district": "Patna", "state": "Bihar",
        "attendance_gap_pct": 42, "camera_uptime_pct": 85,
        "past_findings": 2, "vc_failures": 1, "compliance_days_overdue": 30,
        "reported": [78, 80, 76, 82, 77, 79, 75],
        "observed":  [45, 47, 43, 48, 44, 46, 42],
        "last_inspected": date(2025, 7, 5),
    },
    # MEDIUM RISK
    {
        "name": "Sunrise Apprentice Hub",
        "scheme": "Apprentice", "district": "New Delhi", "state": "Delhi",
        "attendance_gap_pct": 22, "camera_uptime_pct": 90,
        "past_findings": 1, "vc_failures": 1, "compliance_days_overdue": 20,
        "reported": [60, 62, 58, 63, 59, 61, 60],
        "observed":  [47, 49, 45, 51, 46, 48, 46],
        "last_inspected": date(2025, 8, 1),
    },
    {
        "name": "Deccan Skills Academy",
        "scheme": "Skill India", "district": "Hyderabad", "state": "Andhra Pradesh",
        "attendance_gap_pct": 18, "camera_uptime_pct": 91,
        "past_findings": 2, "vc_failures": 0, "compliance_days_overdue": 12,
        "reported": [55, 57, 53, 59, 54, 56, 53],
        "observed":  [45, 47, 43, 49, 44, 46, 44],
        "last_inspected": date(2025, 8, 15),
    },
    {
        "name": "Himalayan Training Centre",
        "scheme": "PMSSS", "district": "Shimla", "state": "Himachal Pradesh",
        "attendance_gap_pct": 15, "camera_uptime_pct": 93,
        "past_findings": 1, "vc_failures": 1, "compliance_days_overdue": 8,
        "reported": [40, 42, 39, 43, 41, 40, 39],
        "observed":  [34, 36, 33, 37, 35, 34, 33],
        "last_inspected": date(2025, 9, 1),
    },
    {
        "name": "Blue Ridge Institute",
        "scheme": "Apprentice", "district": "Pune", "state": "Maharashtra",
        "attendance_gap_pct": 12, "camera_uptime_pct": 95,
        "past_findings": 1, "vc_failures": 0, "compliance_days_overdue": 5,
        "reported": [48, 50, 46, 51, 47, 49, 48],
        "observed":  [42, 44, 41, 45, 42, 43, 42],
        "last_inspected": date(2025, 9, 10),
    },
    # LOW RISK
    {
        "name": "Capital Vocational School",
        "scheme": "Training", "district": "New Delhi", "state": "Delhi",
        "attendance_gap_pct": 5, "camera_uptime_pct": 98,
        "past_findings": 0, "vc_failures": 0, "compliance_days_overdue": 0,
        "reported": [50, 52, 49, 53, 51, 50, 51],
        "observed":  [48, 49, 47, 51, 49, 48, 49],
        "last_inspected": date(2025, 9, 15),
    },
    {
        "name": "Rajputana Skills Hub",
        "scheme": "Skill India", "district": "Jaipur", "state": "Rajasthan",
        "attendance_gap_pct": 4, "camera_uptime_pct": 99,
        "past_findings": 0, "vc_failures": 0, "compliance_days_overdue": 0,
        "reported": [45, 47, 44, 48, 46, 45, 46],
        "observed":  [43, 45, 42, 46, 44, 44, 44],
        "last_inspected": date(2025, 9, 18),
    },
    {
        "name": "Coastal Training Academy",
        "scheme": "PMSSS", "district": "Surat", "state": "Gujarat",
        "attendance_gap_pct": 3, "camera_uptime_pct": 99,
        "past_findings": 0, "vc_failures": 0, "compliance_days_overdue": 0,
        "reported": [38, 40, 37, 41, 39, 38, 39],
        "observed":  [37, 39, 36, 40, 38, 37, 38],
        "last_inspected": date(2025, 9, 20),
    },
]

DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Sample inspection for the highest-risk institution (demo the closed loop)
SAMPLE_INSPECTION = {
    "institution_idx": 0,   # Navjeevan
    "inspector_name": "Ravi Kumar (SIH Inspector)",
    "date": date(2025, 6, 10),
    "beneficiary_present": False,
    "staff_present": True,
    "infrastructure_ok": True,
    "cctv_functional": False,
    "documents_available": False,
    "observations": "Only 43 beneficiaries found on site against 105 reported. CCTV feed was disconnected. Attendance register showed 105 but Aadhaar verification matched only 40.",
    "severity": "CRITICAL",
}


def run():
    print("Creating tables ...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        institution_objects = []
        for idx, inst_data in enumerate(INSTITUTIONS):
            inst = Institution(
                name=inst_data["name"],
                scheme=inst_data["scheme"],
                district=inst_data["district"],
                state=inst_data["state"],
                attendance_gap_pct=inst_data["attendance_gap_pct"],
                camera_uptime_pct=inst_data["camera_uptime_pct"],
                past_findings=inst_data["past_findings"],
                vc_failures=inst_data["vc_failures"],
                compliance_days_overdue=inst_data["compliance_days_overdue"],
                last_inspected=inst_data["last_inspected"],
            )
            db.add(inst)
            db.flush()   # get inst.id

            # Attendance records (7 days)
            base_date = date(2025, 9, 15)  # anchor to recent week
            for day_idx, (rep, obs) in enumerate(zip(inst_data["reported"], inst_data["observed"])):
                record = AttendanceRecord(
                    institution_id=inst.id,
                    date=base_date + timedelta(days=day_idx),
                    day_label=DAY_LABELS[day_idx],
                    reported=rep,
                    observed=obs,
                )
                db.add(record)

            institution_objects.append(inst)

        # Sample past inspection for institution 0
        sample = SAMPLE_INSPECTION
        nav = institution_objects[sample["institution_idx"]]
        insp = Inspection(
            institution_id=nav.id,
            inspector_name=sample["inspector_name"],
            date=sample["date"],
            beneficiary_present=sample["beneficiary_present"],
            staff_present=sample["staff_present"],
            infrastructure_ok=sample["infrastructure_ok"],
            cctv_functional=sample["cctv_functional"],
            documents_available=sample["documents_available"],
            observations=sample["observations"],
            severity=sample["severity"],
        )
        db.add(insp)

        db.commit()
        print(f"Seeded {len(INSTITUTIONS)} institutions with attendance records.")
        print("demo.db ready.")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
