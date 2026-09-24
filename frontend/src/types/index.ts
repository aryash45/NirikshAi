/**
 * Domain types matching backend Pydantic schemas.
 */

export interface AttendanceSeries {
  day: string;
  reported: number;
  observed: number;
}

export interface AttendancePatternResult {
  avg_reported: number;
  avg_observed: number;
  persistent_gap_percent: number;
  is_significant_discrepancy: boolean;
}

export interface RiskDrivers {
  attendance_discrepancy: number; // max 30
  camera_issues: number;          // max 25
  inspection_history: number;     // max 20
  vc_verification: number;        // max 15
  compliance_overdue: number;     // max 10
}

export interface StatsSummary {
  total: number;
  high: number;
  medium: number;
  low: number;
  avg_risk_score: number;
}

export interface InstitutionSummary {
  id: number;
  name: string;
  scheme: string;
  district: string;
  state: string;
  attendance_gap_pct: number;
  camera_uptime_pct: number;
  past_findings: number;
  vc_failures: number;
  compliance_days_overdue: number;
  last_inspected: string | null;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  inspection_probability: number;
  drivers: RiskDrivers;
}

export interface InspectionOut {
  id: number;
  institution_id: number;
  inspector_name: string;
  date: string;
  severity: 'MINOR' | 'MAJOR' | 'CRITICAL';
  observations: string;
}

export interface InstitutionDetail extends InstitutionSummary {
  attendance_series: AttendanceSeries[];
  attendance_pattern: AttendancePatternResult;
  recent_inspections: InspectionOut[];
}

export interface InspectionFindings {
  beneficiary_present: boolean;
  staff_present: boolean;
  infrastructure_ok: boolean;
  cctv_functional: boolean;
  documents_available: boolean;
}

export interface InspectionCreate {
  institution_id: number;
  inspector_name: string;
  date: string;
  findings: InspectionFindings;
  observations: string;
  severity: 'MINOR' | 'MAJOR' | 'CRITICAL';
}

export interface InspectionResponse {
  success: boolean;
  message: string;
  updated_risk: InstitutionSummary;
}

export interface OccupancyPoint {
  second: number;
  count: number;
}

export interface CctvAnalysisResult {
  occupancy_timeline: OccupancyPoint[];
  peak_occupancy: number;
  avg_occupancy: number;
  frames_analyzed: number;
  is_mock: boolean;
}
