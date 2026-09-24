import React from 'react';
import { AttendanceSeries, AttendancePatternResult } from '../types';

interface AttendanceChartProps {
  series: AttendanceSeries[];
  pattern: AttendancePatternResult;
}

export const AttendanceChart: React.FC<AttendanceChartProps> = ({ series, pattern }) => {
  if (!series || series.length === 0) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
        No weekly attendance telemetry recorded.
      </div>
    );
  }

  // Calculate scaling
  const maxVal = Math.max(...series.map((s) => Math.max(s.reported, s.observed, 10)));
  const yMax = Math.ceil((maxVal * 1.15) / 10) * 10;
  const chartHeight = 160;
  const chartWidth = 520;
  const paddingLeft = 40;
  const paddingBottom = 26;
  const paddingTop = 12;
  const paddingRight = 16;

  const innerWidth = chartWidth - paddingLeft - paddingRight;
  const innerHeight = chartHeight - paddingTop - paddingBottom;

  const getX = (index: number) => paddingLeft + (index / (series.length - 1)) * innerWidth;
  const getY = (val: number) => paddingTop + innerHeight - (val / yMax) * innerHeight;

  const reportedPoints = series.map((s, idx) => `${getX(idx)},${getY(s.reported)}`).join(' ');
  const observedPoints = series.map((s, idx) => `${getX(idx)},${getY(s.observed)}`).join(' ');

  return (
    <div style={{ marginTop: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '0.82rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', backgroundColor: 'var(--accent)', borderRadius: '2px' }} />
            <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>Reported (MIS Register)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', backgroundColor: '#6E6E73', borderRadius: '2px' }} />
            <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>Observed (CCTV Headcount)</span>
          </div>
        </div>

        <div style={{
          fontSize: '0.78rem',
          padding: '2px 8px',
          borderRadius: 'var(--radius-xs)',
          backgroundColor: pattern.is_significant_discrepancy ? 'var(--risk-high-bg)' : 'var(--risk-low-bg)',
          color: pattern.is_significant_discrepancy ? 'var(--risk-high-text)' : 'var(--risk-low-text)',
          border: `1px solid ${pattern.is_significant_discrepancy ? 'var(--risk-high-border)' : 'var(--risk-low-border)'}`,
          fontWeight: 600,
        }}>
          {pattern.persistent_gap_percent.toFixed(1)}% Persistent Discrepancy
        </div>
      </div>

      {/* SVG Line Chart */}
      <div style={{ width: '100%', overflowX: 'auto' }}>
        <svg
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          style={{ width: '100%', height: 'auto', display: 'block', backgroundColor: 'var(--surface-raised)', borderRadius: 'var(--radius-sm)' }}
          aria-label="Attendance comparison graph"
          role="img"
        >
          {/* Horizontal Grid lines */}
          {[0, 0.33, 0.66, 1].map((ratio, i) => {
            const y = paddingTop + innerHeight * ratio;
            const labelValue = Math.round(yMax * (1 - ratio));
            return (
              <g key={i}>
                <line
                  x1={paddingLeft}
                  y1={y}
                  x2={chartWidth - paddingRight}
                  y2={y}
                  stroke="var(--border)"
                  strokeWidth="1"
                  strokeDasharray="2 2"
                />
                <text
                  x={paddingLeft - 8}
                  y={y + 3}
                  textAnchor="end"
                  fontSize="9"
                  fill="var(--text-tertiary)"
                  fontFamily="var(--font-mono)"
                >
                  {labelValue}
                </text>
              </g>
            );
          })}

          {/* Area between curves (indicating discrepancy) */}
          <polygon
            points={`${reportedPoints} ${series
              .slice()
              .reverse()
              .map((s, revIdx) => `${getX(series.length - 1 - revIdx)},${getY(s.observed)}`)
              .join(' ')}`}
            fill="var(--accent-subtle)"
            opacity="0.45"
          />

          {/* Reported Line */}
          <polyline
            points={reportedPoints}
            fill="none"
            stroke="var(--accent)"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Observed Line */}
          <polyline
            points={observedPoints}
            fill="none"
            stroke="#6E6E73"
            strokeWidth="2"
            strokeDasharray="4 3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Data Points & Day Labels */}
          {series.map((s, idx) => {
            const x = getX(idx);
            const yRep = getY(s.reported);
            const yObs = getY(s.observed);
            return (
              <g key={idx}>
                {/* Reported circle */}
                <circle cx={x} cy={yRep} r="3.5" fill="var(--accent)" />
                {/* Observed circle */}
                <circle cx={x} cy={yObs} r="3" fill="#6E6E73" />
                {/* X axis Day label */}
                <text
                  x={x}
                  y={chartHeight - 8}
                  textAnchor="middle"
                  fontSize="10"
                  fill="var(--text-secondary)"
                  fontWeight="500"
                >
                  {s.day}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-tertiary)', marginTop: '6px' }}>
        <span>Average Reported: {pattern.avg_reported.toFixed(1)}</span>
        <span>Average Observed: {pattern.avg_observed.toFixed(1)}</span>
        <span>Signal Status: {pattern.is_significant_discrepancy ? 'Flagged for Surprise Inspection' : 'Within Expected Bounds'}</span>
      </div>
    </div>
  );
};
