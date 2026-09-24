import React from 'react';
import { StatsSummary } from '../types';

interface StatsOverviewProps {
  stats: StatsSummary | null;
  loading: boolean;
}

export const StatsOverview: React.FC<StatsOverviewProps> = ({ stats, loading }) => {
  return (
    <section style={{ padding: '28px 0 20px 0' }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px',
      }}>
        {/* Monitored Centers */}
        <div className="card" style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
            Monitored Training Centers
          </div>
          <div style={{ fontSize: '1.9rem', fontWeight: 600, marginTop: '6px', color: 'var(--text-primary)' }}>
            {loading || !stats ? <span className="skeleton" style={{ display: 'inline-block', width: '48px', height: '28px' }} /> : stats.total}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)', marginTop: '4px' }}>
            Active across Skill India, PMSSS, Apprenticeship
          </div>
        </div>

        {/* High Risk Centers */}
        <div className="card" style={{ padding: '16px 20px', borderLeft: '3px solid var(--risk-high-text)' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--risk-high-text)', fontWeight: 600 }}>
            Immediate Inspection Flags
          </div>
          <div style={{ fontSize: '1.9rem', fontWeight: 600, marginTop: '6px', color: 'var(--risk-high-text)' }}>
            {loading || !stats ? <span className="skeleton" style={{ display: 'inline-block', width: '32px', height: '28px' }} /> : stats.high}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)', marginTop: '4px' }}>
            Risk rating equal or greater than 60 points
          </div>
        </div>

        {/* Medium Risk Centers */}
        <div className="card" style={{ padding: '16px 20px', borderLeft: '3px solid var(--risk-medium-text)' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--risk-medium-text)', fontWeight: 600 }}>
            Elevated Watchlist Centers
          </div>
          <div style={{ fontSize: '1.9rem', fontWeight: 600, marginTop: '6px', color: 'var(--risk-medium-text)' }}>
            {loading || !stats ? <span className="skeleton" style={{ display: 'inline-block', width: '32px', height: '28px' }} /> : stats.medium}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)', marginTop: '4px' }}>
            Risk rating between 30 and 59 points
          </div>
        </div>

        {/* Average Risk Rating */}
        <div className="card" style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
            System Average Risk Score
          </div>
          <div style={{ fontSize: '1.9rem', fontWeight: 600, marginTop: '6px', color: 'var(--text-primary)' }}>
            {loading || !stats ? (
              <span className="skeleton" style={{ display: 'inline-block', width: '56px', height: '28px' }} />
            ) : (
              `${stats.avg_risk_score.toFixed(1)} / 100`
            )}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)', marginTop: '4px' }}>
            Weighted formula across 5 audit signals
          </div>
        </div>
      </div>
    </section>
  );
};
