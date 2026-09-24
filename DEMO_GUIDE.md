# NirikshAi: SIH 26095 Enterprise Implementation & Demo Guide

**Repository:** [aryash45/NirikshAi](https://github.com/aryash45/NirikshAi)  
**Problem Statement:** SIH26095 – Smart Real-Time Monitoring & Inspection Mobile App  
**Ministry:** Ministry of Social Justice and Empowerment (MSJE)

---

## 🚀 Newly Implemented Capabilities

In response to the SIH 2026 reviewer feedback, the core missing modules have been engineered and tested end-to-end:

| Reviewer Critique | Engineering Solution |
| :--- | :--- |
| **"Where is the Mobile Inspection App?"** | Built **Mobile Field Inspector PWA** with interactive iPhone frame simulator, offline mode simulator with `localStorage` persistent queue, and auto-sync on reconnect. |
| **"Can officers upload fake/recycled photos?"** | Engineered **Evidence Integrity & Anti-Tampering Engine** using SHA-256 + 64-bit Difference Perceptual Hashing (dHash) to detect identical or edited recycled photos (>90% match) with GPS telemetry validation. |
| **"How are inspectors assigned?"** | Engineered **Smart Inspector Matcher** with jurisdiction filtering, conflict-of-interest exclusion, workload balancing, and priority multiplier (7x for high-risk centers). |
| **"Different schemes require different audits"** | Created **Dynamic Statutory Compliance Checklists** tailored for *Skill India*, *PMSSS*, and *Apprenticeship Promotion Scheme*. |

---

## 🎙️ 5-Minute Live Judging Presentation Script

When demonstrating NirikshAi to SIH judges or evaluators, follow this high-impact 4-step sequence:

### Step 1: The Problem & Live Telemetry (1 Minute)
- Open `http://localhost:5173` on the **Institutions Directory** tab.
- *Pitch point:* "Traditional inspections rely on random audits or post-facto complaints. NirikshAi operates on automated discrepancy detection: comparing self-reported register logs against actual surveillance headcounts to calculate an objective risk score."
- Point out `#1 Navjeevan Skill Centre` (Risk: 84.0/100, 57.4% attendance discrepancy gap).

### Step 2: Computer Vision CCTV Verification (1 Minute)
- Switch to the **CCTV Verification** tab.
- Click **Run Computer Vision Verification (Mock Video)**.
- *Pitch point:* "Our YOLOv8 human-detection pipeline computes classroom occupancy across 30 one-second frames. We extract temporal peaks and average occupancy without facial recognition or biometric storage, strictly complying with the Digital Personal Data Protection (DPDP) Act 2023."

### Step 3: Smart Inspector Dispatcher (1 Minute)
- Switch to the **📱 Field Inspector App** tab.
- Click **⚡ Run Smart Inspector Matcher Algorithm**.
- *Pitch point:* "High-risk institutions trigger a 7x priority dispatch multiplier. Our matcher filters certified officers by state jurisdiction, excludes any conflict of interest, balances caseloads, and assigns an official dispatch code (e.g. `DSP-2026-4091`)."

### Step 4: Anti-Tampering Engine & Offline Capability (2 Minutes - The "WOW" Moment)
- In the mobile view, toggle **Offline Mode**.
  - *Pitch point:* "Remote skill centers in rural districts often have zero cellular connectivity. NirikshAi stores completed statutory checklists, GPS telemetry, and photos in an encrypted local sync queue."
- Click **🚨 Test Duplicate Detector**.
  - *Pitch point:* "What happens if a corrupt field officer submits last month's photo or a stock image? NirikshAi calculates a 64-bit Difference Perceptual Hash (dHash) and compares it with historical inspection archives. The system instantly flags a **97.8% visual similarity fraud alert** and rejects recycled evidence."
- Toggle back to **Online Mode** and click **Submit & Sync Inspection to HQ**.
  - Show how the backend recalculates the institution risk in real-time, completing the closed-loop audit lifecycle.
