"""
Quick smoke test for all backend endpoints.
Supports both live running server (http://localhost:8000) and in-process TestClient.
"""

import os
import sys

# Ensure UTF-8 output on Windows terminals
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import httpx
from app.main import app

BASE = "http://localhost:8000"


def run_tests():
    # Detect if live server is reachable, otherwise use in-memory TestClient
    client = None
    try:
        r = httpx.get(f"{BASE}/", timeout=0.5)
        print("[*] Testing against LIVE server on http://localhost:8000\n")
        client = httpx.Client(base_url=BASE)
    except Exception:
        print("[*] Live server not detected on :8000. Running with FastAPI TestClient...\n")
        from fastapi.testclient import TestClient
        client = TestClient(app)

    def ok(label, r):
        status = "[OK]" if r.status_code < 300 else "[FAIL]"
        print(f"{status} {label}: HTTP {r.status_code}")
        if r.status_code >= 300:
            print(f"   Response: {r.text}")
        return r.status_code < 300

    try:
        # 1. Health
        r = client.get("/")
        assert ok("GET /", r)

        # 2. Institutions list
        r = client.get("/api/institutions")
        assert ok("GET /api/institutions", r)
        insts = r.json()
        print(f"   -> {len(insts)} institutions returned, sorted by risk:")
        for i in insts:
            print(f"      [{i['risk_level']:6}] {i['name']:35} score={i['risk_score']}")

        # 3. Stats
        r = client.get("/api/stats/summary")
        assert ok("GET /api/stats/summary", r)
        print(f"   -> {r.json()}")

        # 4. Institution detail (highest risk)
        top = insts[0]
        r = client.get(f"/api/institutions/{top['id']}")
        assert ok(f"GET /api/institutions/{top['id']}", r)
        d = r.json()
        print(f"   -> attendance days: {len(d['attendance_series'])}, gap: {d['attendance_pattern']['persistent_gap_percent']}%")
        print(f"   -> discrepancy flag: {d['attendance_pattern']['is_significant_discrepancy']}")

        # 5. Submit inspection (closed-loop demo)
        payload = {
            "institution_id": top["id"],
            "inspector_name": "Test Inspector",
            "date": "2026-09-23",
            "findings": {
                "beneficiary_present": False,
                "staff_present": True,
                "infrastructure_ok": True,
                "cctv_functional": False,
                "documents_available": False,
            },
            "observations": "Attendance inflated. CCTV offline. Only 40 of 105 reported present.",
            "severity": "CRITICAL",
        }
        r = client.post("/api/inspections", json=payload)
        assert ok("POST /api/inspections", r)
        resp = r.json()
        print(f"   -> message: {resp['message']}")
        print(f"   -> new risk: {resp['updated_risk']['risk_score']} [{resp['updated_risk']['risk_level']}]")
        old_score = top["risk_score"]
        new_score = resp["updated_risk"]["risk_score"]
        delta = round(new_score - old_score, 1)
        print(f"   -> score delta: {old_score} -> {new_score} ({'+' if delta >= 0 else ''}{delta})")

        # 6. CCTV mock
        r = client.get("/api/cctv/mock")
        assert ok("GET /api/cctv/mock", r)
        cv = r.json()
        print(f"   -> peak={cv['peak_occupancy']}, avg={cv['avg_occupancy']}, points={len(cv['occupancy_timeline'])}, is_mock={cv['is_mock']}")

        print("\nAll endpoints verified! Professional architecture is fully functional.")

    except Exception as e:
        print(f"\n[FAIL] Error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
