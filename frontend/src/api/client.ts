/**
 * API client communicating with FastAPI backend.
 */

import {
  StatsSummary,
  InstitutionSummary,
  InstitutionDetail,
  InspectionCreate,
  InspectionResponse,
  CctvAnalysisResult,
  SchemeChecklist,
  InspectorProfile,
  InspectionScheduleResponse,
  EvidenceValidationResult,
} from '../types';

const API_BASE = '/api';

export async function fetchStatsSummary(): Promise<StatsSummary> {
  const res = await fetch(`${API_BASE}/stats/summary`);
  if (!res.ok) throw new Error(`Failed to fetch stats: ${res.statusText}`);
  return res.json();
}

export async function fetchInstitutions(): Promise<InstitutionSummary[]> {
  const res = await fetch(`${API_BASE}/institutions`);
  if (!res.ok) throw new Error(`Failed to fetch institutions: ${res.statusText}`);
  return res.json();
}

export async function fetchInstitutionDetail(id: number): Promise<InstitutionDetail> {
  const res = await fetch(`${API_BASE}/institutions/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch institution #${id}: ${res.statusText}`);
  return res.json();
}

export async function submitInspection(payload: InspectionCreate): Promise<InspectionResponse> {
  const res = await fetch(`${API_BASE}/inspections`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Failed to submit inspection');
  }
  return res.json();
}

export async function recalculateRisk(id: number): Promise<InstitutionSummary> {
  const res = await fetch(`${API_BASE}/institutions/${id}/risk/recalculate`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Failed to recalculate risk: ${res.statusText}`);
  return res.json();
}

export async function fetchCctvMock(): Promise<CctvAnalysisResult> {
  const res = await fetch(`${API_BASE}/cctv/mock`);
  if (!res.ok) throw new Error(`Failed to fetch CCTV mock: ${res.statusText}`);
  return res.json();
}

export async function analyzeCctvVideo(file: File): Promise<CctvAnalysisResult> {
  const formData = new FormData();
  formData.append('video', file);
  const res = await fetch(`${API_BASE}/cctv/analyze`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Failed to analyze video');
  }
  return res.json();
}

export async function fetchSchemeChecklist(scheme: string): Promise<SchemeChecklist> {
  const res = await fetch(`${API_BASE}/field-audit/checklists/${encodeURIComponent(scheme)}`);
  if (!res.ok) throw new Error(`Failed to fetch checklist for ${scheme}: ${res.statusText}`);
  return res.json();
}

export async function fetchInspectors(): Promise<InspectorProfile[]> {
  const res = await fetch(`${API_BASE}/field-audit/inspectors`);
  if (!res.ok) throw new Error(`Failed to fetch inspectors: ${res.statusText}`);
  return res.json();
}

export async function scheduleInspection(institutionId: number, targetDate?: string): Promise<InspectionScheduleResponse> {
  const res = await fetch(`${API_BASE}/field-audit/schedule`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ institution_id: institutionId, target_date: targetDate }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Failed to schedule inspection');
  }
  return res.json();
}

export async function validateEvidencePhoto(
  file: File,
  simulateDuplicate: boolean = false
): Promise<EvidenceValidationResult> {
  const formData = new FormData();
  formData.append('file', file);
  const queryParam = simulateDuplicate ? '?simulate_duplicate=true' : '';
  const res = await fetch(`${API_BASE}/field-audit/evidence/validate${queryParam}`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Failed to validate evidence');
  }
  return res.json();
}

export function subscribeToRiskUpdates(
  onUpdate: (data: { institution_id: number; data: InstitutionSummary }) => void
): () => void {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/risk-updates`;
  let socket: WebSocket | null = null;
  let isClosedManually = false;

  try {
    socket = new WebSocket(wsUrl);
    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event === 'RISK_UPDATED') {
          onUpdate(payload);
        }
      } catch (err) {
        console.error('Error parsing risk WebSocket message', err);
      }
    };
    socket.onerror = () => {
      // WebSocket errors will fallback to manual polling gracefully
    };
  } catch {
    // If WebSocket fails, application stays functional
  }

  return () => {
    isClosedManually = true;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.close();
    }
  };
}
