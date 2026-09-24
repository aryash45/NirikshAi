import React from 'react';
import { RiskDrivers } from '../types';

interface RiskDriversBarProps {
  drivers: RiskDrivers;
}

interface FactorMeta {
  key: keyof RiskDrivers;
  label: string;
  max: number;
  description: string;
}

const FACTORS: FactorMeta[] = [
  { key: 'attendance_discrepancy', label: 'Attendance Discrepancy', max: 30, description: 'Inflated attendance gap vs CCTV' },
  { key: 'camera_issues', label: 'Camera Downtime', max: 25, description: 'Offline feeds and missing streams' },
  { key: 'inspection_history', label: 'Unresolved Past Findings', max: 20, description: 'Non-conformities from previous visits' },
  { key: 'vc_verification', label: 'VC Verification Failures', max: 15, description: 'Failed unannounced video calls' },
  { key: 'compliance_overdue', label: 'Compliance Delays', max: 10, description: 'Days overdue on statutory filings' },
];

export const RiskDriversBar: React.FC<RiskDriversBarProps> = ({ drivers }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
      {FACTORS.map((f) => {
        const val = drivers[f.key] || 0;
        const pct = Math.min(100, Math.max(0, (val / f.max) * 100));

        return (
          <div key={f.key}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '4px' }}>
              <div>
                <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                  {f.label}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginLeft: '6px' }}>
                  ({f.description})
                </span>
              </div>
              <span style={{ fontSize: '0.82rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>
                {val.toFixed(1)} / {f.max} pts
              </span>
            </div>

            {/* Proportional Bar */}
            <div style={{
              height: '6px',
              backgroundColor: 'var(--surface-subtle)',
              borderRadius: 'var(--radius-xs)',
              overflow: 'hidden',
              display: 'flex',
            }}>
              <div
                style={{
                  width: `${pct}%`,
                  backgroundColor: pct > 65 ? 'var(--risk-high-text)' : pct > 35 ? 'var(--risk-medium-text)' : 'var(--accent)',
                  transition: 'width var(--transition-normal)',
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};
