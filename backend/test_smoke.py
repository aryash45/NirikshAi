"""
Comprehensive Smoke and Integration Test Suite for NirikshAi.
Tests all endpoints including Auth, RBAC, GPS Geofencing, Idempotent Inspections,
Evidence Integrity (dHash/SHA-256), Smart Dispatch, and Cryptographic Audit Chain.
Supports both live running server (http://localhost:8000) and in-process TestClient.
"""

from __future__ import annotations

import io
import os
import sys
import uuid
from typing import Optional

# Ensure UTF-8 output on Windows terminals
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import httpx
from PIL import Image
from app.main import app

BASE = "http://localhost:8000"


def run_tests():
    # Detect if live server is reachable, otherwise use in-memory TestClient
    client: Optional[httpx.Client] = None
    try:
        r = httpx.get(f"{BASE}/", timeout=1.0)
        print("[*] Testing against LIVE server on http://localhost:8000\n")
        client = httpx.Client(base_url=BASE, timeout=10.0)
    except Exception:
        print("[*] Live server not detected on :8000. Running with FastAPI TestClient...\n")
        from fastapi.testclient import TestClient
        client = TestClient(app)

    def check(label: str, r: httpx.Response, expected_status: int = 200) -> bool:
        ok = r.status_code == expected_status
        status_tag = "[PASS]" if ok else "[FAIL]"
        print(f"{status_tag} {label} (HTTP {r.status_code}, expected {expected_status})")
        if not ok:
            print(f"       Response: {r.text[:300]}")
        return ok

    passed_count = 0
    total_count = 0

    def record(success: bool):
        nonlocal passed_count, total_count
        total_count += 1
        if success:
            passed_count += 1

    try:
        # ── 1. System Health ───────────────────────────────────────────────
        r = client.get("/")
        record(check("1. Root Health Check", r, 200))
        data = r.json()
        assert data.get("status") == "running"
        assert data.get("service") == "NirikshAi API"

        # ── 2. Authentication & JWT ───────────────────────────────────────
        # 2a. Valid Login (HQ Officer)
        r = client.post(
            "/api/auth/login",
            json={"username": "hq_officer", "password": "hq_password123"},
        )
        record(check("2a. Auth Login (Valid HQ Officer)", r, 200))
        hq_token = r.json()["access_token"]
        assert len(hq_token) > 20

        # 2b. Valid Login (Inspector)
        r = client.post(
            "/api/auth/login",
            json={"username": "inspector1", "password": "field_pass123"},
        )
        record(check("2b. Auth Login (Valid Inspector)", r, 200))
        insp_token = r.json()["access_token"]

        # 2c. Invalid Login Rejection
        r = client.post(
            "/api/auth/login",
            json={"username": "hq_officer", "password": "wrong_password"},
        )
        record(check("2c. Auth Login (Invalid Password Rejection)", r, 401))

        # 2d. Authenticated User Profile
        r = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {hq_token}"},
        )
        record(check("2d. Auth Profile (/api/auth/me)", r, 200))
        assert r.json()["role"] == "HQ_OFFICER"

        # ── 3. Institutions Directory ──────────────────────────────────────
        r = client.get(
            "/api/institutions",
            headers={"Authorization": f"Bearer {hq_token}"},
        )
        record(check("3a. Institutions List (Sorted by Risk)", r, 200))
        insts = r.json()
        assert len(insts) > 0
        top = insts[0]
        print(f"       Top high-risk target: {top['name']} (Score: {top['risk_score']}, Level: {top['risk_level']})")

        # 3b. Institution Detail
        r = client.get(
            f"/api/institutions/{top['id']}",
            headers={"Authorization": f"Bearer {hq_token}"},
        )
        record(check(f"3b. Institution Detail (#{top['id']})", r, 200))
        detail = r.json()
        assert len(detail["attendance_series"]) == 7

        # ── 4. Global Stats Summary ────────────────────────────────────────
        r = client.get("/api/stats/summary")
        record(check("4. Stats Summary", r, 200))

        # ── 5. GPS Geofencing Validation ───────────────────────────────────
        # 5a. GPS On-Site (Inspector within Lucknow geofence)
        on_site_payload = {
            "institution_id": top["id"],
            "inspector_lat": 26.8467,
            "inspector_lng": 80.9462,
            "accuracy_meters": 8.5,
        }
        r = client.post(
            "/api/gps/validate",
            json=on_site_payload,
            headers={"Authorization": f"Bearer {insp_token}"},
        )
        record(check("5a. GPS Validation (Within Geofence)", r, 200))
        gps_res = r.json()
        assert gps_res["status"] == "ON_SITE"
        print(f"       Distance: {gps_res['distance_meters']}m (Allowed radius: {gps_res['allowed_radius_meters']}m)")

        # 5b. GPS Off-Site (Outside geofence)
        off_site_payload = {
            "institution_id": top["id"],
            "inspector_lat": 26.8467 + 0.05,  # ~5.5 km away
            "inspector_lng": 80.9462 + 0.05,
            "accuracy_meters": 12.0,
        }
        r = client.post(
            "/api/gps/validate",
            json=off_site_payload,
            headers={"Authorization": f"Bearer {insp_token}"},
        )
        record(check("5b. GPS Validation (Outside Geofence Detection)", r, 200))
        gps_off_res = r.json()
        assert gps_off_res["status"] == "OUTSIDE_GEOFENCE"

        # ── 6. Idempotent Inspection Submission ────────────────────────────
        idem_key = f"smoke-test-{uuid.uuid4()}"
        inspection_payload = {
            "institution_id": top["id"],
            "inspector_name": "Ravi Kumar Sharma",
            "date": "2026-09-25",
            "findings": {
                "beneficiary_present": False,
                "staff_present": True,
                "infrastructure_ok": True,
                "cctv_functional": False,
                "documents_available": False,
            },
            "observations": "Automated smoke test: attendance mismatch confirmed on-site.",
            "severity": "CRITICAL",
        }
        headers = {
            "Authorization": f"Bearer {insp_token}",
            "X-Idempotency-Key": idem_key,
        }

        # 6a. First Submission
        r = client.post("/api/inspections", json=inspection_payload, headers=headers)
        record(check("6a. Submit Inspection with Idempotency Key", r, 200))
        insp_res = r.json()
        assert "updated_risk" in insp_res

        # 6b. Duplicate Submission with Same Key (Must be rejected with 409)
        r_dup = client.post("/api/inspections", json=inspection_payload, headers=headers)
        record(check("6b. Idempotent Duplicate Inspection Rejection (409)", r_dup, 409))

        # ── 7. Cryptographic Audit Trail Verification ──────────────────────
        r = client.get(
            "/api/audit/events?limit=10",
            headers={"Authorization": f"Bearer {hq_token}"},
        )
        record(check("7a. Retrieve Audit Log Trail", r, 200))
        events_list = r.json()
        assert len(events_list) > 0

        r = client.get(
            "/api/audit/verify-chain",
            headers={"Authorization": f"Bearer {hq_token}"},
        )
        record(check("7b. Verify Audit Trail Cryptographic Hash-Chain", r, 200))
        verify_data = r.json()
        assert verify_data["valid"] is True
        assert verify_data["chain_status"] == "AUDIT_CHAIN_VALID"
        print(f"       Audit chain verified valid across {verify_data['total_events']} events")

        # ── 8. Field Officer Smart Dispatch & Dynamic Checklist ───────────
        # 8a. Dynamic Statutory Checklist
        r = client.get("/api/field-audit/checklists/Skill India")
        record(check("8a. Scheme Statutory Checklist (Skill India)", r, 200))
        checklist = r.json()
        assert len(checklist["items"]) > 0

        # 8b. Certified Inspectors
        r = client.get("/api/field-audit/inspectors")
        record(check("8b. Available Certified Field Inspectors", r, 200))

        # 8c. Cryptographic Dispatch Schedule
        r = client.post(
            "/api/field-audit/schedule",
            json={"institution_id": top["id"]},
            headers={"Authorization": f"Bearer {hq_token}"},
        )
        record(check("8c. Cryptographic Inspector Dispatch Assignment", r, 200))
        dispatch = r.json()
        assert dispatch["dispatch_code"].startswith("DISP-")

        # ── 9. Evidence Integrity & File MIME Validation ───────────────────
        # 9a. Authentic Image Validation
        img = Image.new("RGB", (64, 64), color="forestgreen")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        test_bytes = buf.getvalue()

        files = {"file": ("inspection_onsite.jpg", test_bytes, "image/jpeg")}
        r = client.post(
            "/api/field-audit/evidence/validate",
            files=files,
            headers={"Authorization": f"Bearer {insp_token}"},
        )
        record(check("9a. Evidence Validation (Authentic JPEG with SHA-256 & dHash)", r, 200))
        ev_data = r.json()
        assert ev_data["is_valid"] is True
        assert len(ev_data["sha256_hash"]) == 64
        assert ev_data["perceptual_hash"] is not None

        # 9b. Malicious / Non-Image File Rejection
        fake_files = {"file": ("malicious_script.jpg", b"MALICIOUS_NON_IMAGE_DATA_BYTES_PAYLOAD", "image/jpeg")}
        r = client.post(
            "/api/field-audit/evidence/validate",
            files=fake_files,
            headers={"Authorization": f"Bearer {insp_token}"},
        )
        record(check("9b. Magic Byte Rejection of Corrupt/Fake Image", r, 200))
        fake_res = r.json()
        assert fake_res["is_valid"] is False
        assert fake_res["integrity_status"] == "REJECTED"

        # ── 10. CCTV Analytics & Stream Verification ───────────────────────
        r = client.get("/api/cctv/mock")
        record(check("10. CCTV Stream & Headcount Verification", r, 200))
        cctv_data = r.json()
        assert "occupancy_timeline" in cctv_data
        assert len(cctv_data["occupancy_timeline"]) > 0

        # ── Test Summary ───────────────────────────────────────────────────
        print(f"\n=======================================================")
        print(f"Smoke Test Summary: {passed_count}/{total_count} assertions PASSED.")
        print(f"=======================================================\n")

        if passed_count < total_count:
            print("[FAIL] Some tests did not meet expectations.")
            sys.exit(1)
        else:
            print("[SUCCESS] All endpoints, services, security controls, and audit trails operational.")

    except Exception as e:
        print(f"\n[FAIL] Unexpected error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
