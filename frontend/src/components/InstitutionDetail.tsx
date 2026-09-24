import React, { useState } from 'react';
import { InstitutionDetail as InstitutionDetailType, InspectionResponse } from '../types';
import { AttendanceChart } from './AttendanceChart';
import { RiskDriversBar } from './RiskDriversBar';
import { InspectionModal } from './InspectionModal';
import { formatDate, getRiskLevelClass } from '../utils/formatters';

interface InstitutionDetailProps {
  institution: InstitutionDetailType | null;
  loading: boolean;
  onInspectionUpdated: (response: InspectionResponse) => void;
  onRefresh: () => void;
}

export const InstitutionDetail: React.FC<InstitutionDetailProps> = ({
  institution,
  loading,
  onInspectionUpdated,
  onRefresh,
}) => {
  const [modalOpen, setModalOpen] = useState(false);

  if (loading) {
    return (
      <div className="card" style={{ padding: '24px', minHeight: '380px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="skeleton" style={{ width: '40%', height: '24px' }} />
        <div className="skeleton" style={{ width: '60%', height: '16px' }} />
        <div className="skeleton" style={{ width: '100%', height: '180px', marginTop: '12px' }} />
      </div>
    );
  }

  if (!institution) {
    return (
      <div className="card" style={{ padding: '48px 24px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
        <div style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--text-secondary)' }}>
          Select an institution from the directory
        </div>
        <p style={{ fontSize: '0.84rem', marginTop: '4px' }}>
          Inspect discrepancy telemetry, 5-factor risk drivers, and past visit logs.
        </p>
      </div>
    );
  }

  const riskClass = getRiskLevelClass(institution.risk_level);

  return (
    <div className="card" style={{ padding: '24px' }}>
      {/* Detail Header */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        gap: '12px',
        borderBottom: '1px solid var(--border)',
        paddingBottom: '16px',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <h2 style={{ fontSize: '1.25rem' }}>{institution.name}</h2>
            <span className={`risk-badge ${riskClass}`}>
              {institution.risk_level} RISK ({institution.risk_score.toFixed(1)})
            </span>
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            {institution.scheme} Scheme • {institution.district}, {institution.state} • Last Visited: {formatDate(institution.last_inspected)}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className="btn btn-secondary"
            onClick={onRefresh}
            style={{ fontSize: '0.84rem', padding: '6px 12px' }}
          >
            Refresh
          </button>
          <button
            className="btn btn-primary"
            onClick={() => setModalOpen(true)}
            style={{ fontSize: '0.84rem', padding: '6px 14px' }}
          >
            Conduct Inspection
          </button>
        </div>
      </div>

      {/* Primary Telemetry Metrics Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: '12px',
        padding: '16px 0',
        borderBottom: '1px solid var(--border)',
      }}>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
            Camera Uptime
          </div>
          <div style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
            {institution.camera_uptime_pct.toFixed(1)}%
          </div>
        </div>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
            Attendance Gap
          </div>
          <div style={{ fontSize: '1.15rem', fontWeight: 600, color: institution.attendance_gap_pct > 20 ? 'var(--risk-high-text)' : 'var(--text-primary)', marginTop: '2px' }}>
            {institution.attendance_gap_pct.toFixed(1)}%
          </div>
        </div>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
            Past Findings
          </div>
          <div style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
            {institution.past_findings} unresolved
          </div>
        </div>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
            VC Failures
          </div>
          <div style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
            {institution.vc_failures} calls
          </div>
        </div>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
            Overdue Days
          </div>
          <div style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
            {institution.compliance_days_overdue} days
          </div>
        </div>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
            Inspection Weight
          </div>
          <div style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--accent)', marginTop: '2px' }}>
            {institution.inspection_probability}× multiplier
          </div>
        </div>
      </div>

      {/* 7-Day Attendance Discrepancy Graph */}
      <div style={{ marginTop: '20px' }}>
        <h3 style={{ fontSize: '0.96rem', letterSpacing: '-0.01em' }}>
          7-Day Telemetry: MIS Register vs CCTV Headcount
        </h3>
        <p style={{ fontSize: '0.78rem', marginTop: '2px' }}>
          Compares self-reported batch size against automated vision headcounts across the week.
        </p>
        <AttendanceChart series={institution.attendance_series} pattern={institution.attendance_pattern} />
      </div>

      {/* 5-Factor Risk Score Drivers */}
      <div style={{ marginTop: '24px', paddingTop: '20px', borderTop: '1px solid var(--border)' }}>
        <h3 style={{ fontSize: '0.96rem', letterSpacing: '-0.01em' }}>
          Explainable Risk Drivers ({institution.risk_score.toFixed(1)} / 100 Total)
        </h3>
        <p style={{ fontSize: '0.78rem', marginTop: '2px' }}>
          Proportional breakdown explaining why this center was prioritized for verification.
        </p>
        <RiskDriversBar drivers={institution.drivers} />
      </div>

      {/* Past Inspections History */}
      <div style={{ marginTop: '24px', paddingTop: '20px', borderTop: '1px solid var(--border)' }}>
        <h3 style={{ fontSize: '0.96rem', letterSpacing: '-0.01em', marginBottom: '8px' }}>
          Recent Inspection Records
        </h3>
        {institution.recent_inspections.length === 0 ? (
          <div style={{ fontSize: '0.82rem', color: 'var(--text-tertiary)', fontStyle: 'italic' }}>
            No past physical audits on record. First inspection will establish baseline.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {institution.recent_inspections.map((insp) => (
              <div
                key={insp.id}
                style={{
                  padding: '10px 12px',
                  backgroundColor: 'var(--surface-raised)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.82rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontWeight: 600 }}>{insp.inspector_name}</span>
                  <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                    {formatDate(insp.date)} • {insp.severity}
                  </span>
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  {insp.observations}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Inspection Modal */}
      <InspectionModal
        institution={institution}
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSuccess={onInspectionUpdated}
      />
    </div>
  );
};
