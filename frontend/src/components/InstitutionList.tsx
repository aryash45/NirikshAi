import React, { useState, useMemo } from 'react';
import { InstitutionSummary } from '../types';
import { formatDate, getRiskLevelClass } from '../utils/formatters';

interface InstitutionListProps {
  institutions: InstitutionSummary[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  loading: boolean;
}

export const InstitutionList: React.FC<InstitutionListProps> = ({
  institutions,
  selectedId,
  onSelect,
  loading,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL');

  const filteredInstitutions = useMemo(() => {
    return institutions.filter((inst) => {
      const matchesSearch =
        inst.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        inst.district.toLowerCase().includes(searchTerm.toLowerCase()) ||
        inst.state.toLowerCase().includes(searchTerm.toLowerCase()) ||
        inst.scheme.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesFilter =
        selectedFilter === 'ALL' || inst.risk_level === selectedFilter;

      return matchesSearch && matchesFilter;
    });
  }, [institutions, searchTerm, selectedFilter]);

  const counts = useMemo(() => {
    return {
      all: institutions.length,
      high: institutions.filter((i) => i.risk_level === 'HIGH').length,
      medium: institutions.filter((i) => i.risk_level === 'MEDIUM').length,
      low: institutions.filter((i) => i.risk_level === 'LOW').length,
    };
  }, [institutions]);

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Search and Filters Header */}
      <div style={{ padding: '16px', borderBottom: '1px solid var(--border)' }}>
        <input
          type="search"
          placeholder="Search by center, state, district, or scheme..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          aria-label="Search institutions"
          style={{ marginBottom: '12px' }}
        />

        {/* Filter Pills */}
        <div style={{ display: 'flex', gap: '6px', overflowX: 'auto' }}>
          <button
            onClick={() => setSelectedFilter('ALL')}
            style={{
              padding: '4px 10px',
              fontSize: '0.78rem',
              fontWeight: 500,
              borderRadius: 'var(--radius-xs)',
              border: '1px solid',
              borderColor: selectedFilter === 'ALL' ? 'var(--accent)' : 'var(--border)',
              backgroundColor: selectedFilter === 'ALL' ? 'var(--accent-subtle)' : 'var(--surface)',
              color: selectedFilter === 'ALL' ? 'var(--accent)' : 'var(--text-secondary)',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            All ({counts.all})
          </button>
          <button
            onClick={() => setSelectedFilter('HIGH')}
            style={{
              padding: '4px 10px',
              fontSize: '0.78rem',
              fontWeight: 500,
              borderRadius: 'var(--radius-xs)',
              border: '1px solid',
              borderColor: selectedFilter === 'HIGH' ? 'var(--risk-high-text)' : 'var(--border)',
              backgroundColor: selectedFilter === 'HIGH' ? 'var(--risk-high-bg)' : 'var(--surface)',
              color: selectedFilter === 'HIGH' ? 'var(--risk-high-text)' : 'var(--text-secondary)',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            High Risk ({counts.high})
          </button>
          <button
            onClick={() => setSelectedFilter('MEDIUM')}
            style={{
              padding: '4px 10px',
              fontSize: '0.78rem',
              fontWeight: 500,
              borderRadius: 'var(--radius-xs)',
              border: '1px solid',
              borderColor: selectedFilter === 'MEDIUM' ? 'var(--risk-medium-text)' : 'var(--border)',
              backgroundColor: selectedFilter === 'MEDIUM' ? 'var(--risk-medium-bg)' : 'var(--surface)',
              color: selectedFilter === 'MEDIUM' ? 'var(--risk-medium-text)' : 'var(--text-secondary)',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            Medium ({counts.medium})
          </button>
          <button
            onClick={() => setSelectedFilter('LOW')}
            style={{
              padding: '4px 10px',
              fontSize: '0.78rem',
              fontWeight: 500,
              borderRadius: 'var(--radius-xs)',
              border: '1px solid',
              borderColor: selectedFilter === 'LOW' ? 'var(--risk-low-text)' : 'var(--border)',
              backgroundColor: selectedFilter === 'LOW' ? 'var(--risk-low-bg)' : 'var(--surface)',
              color: selectedFilter === 'LOW' ? 'var(--risk-low-text)' : 'var(--text-secondary)',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            Low ({counts.low})
          </button>
        </div>
      </div>

      {/* Institution List Items */}
      <div style={{ flex: 1, overflowY: 'auto', maxHeight: '580px' }}>
        {loading ? (
          <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="skeleton" style={{ width: '100%', height: '64px' }} />
            ))}
          </div>
        ) : filteredInstitutions.length === 0 ? (
          <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: '0.86rem' }}>
            No centers match the filter criteria.
          </div>
        ) : (
          filteredInstitutions.map((inst) => {
            const isSelected = inst.id === selectedId;
            const riskClass = getRiskLevelClass(inst.risk_level);

            return (
              <div
                key={inst.id}
                role="button"
                tabIndex={0}
                onClick={() => onSelect(inst.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') onSelect(inst.id);
                }}
                style={{
                  padding: '14px 16px',
                  borderBottom: '1px solid var(--border-subtle)',
                  cursor: 'pointer',
                  backgroundColor: isSelected ? 'var(--accent-subtle)' : 'transparent',
                  borderLeft: isSelected ? '3px solid var(--accent)' : '3px solid transparent',
                  transition: 'background-color var(--transition-fast)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: '8px' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-primary)' }}>
                    {inst.name}
                  </div>
                  <span className={`risk-badge ${riskClass}`}>
                    {inst.risk_score.toFixed(1)}
                  </span>
                </div>

                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  {inst.scheme} • {inst.district}, {inst.state}
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', color: 'var(--text-tertiary)', marginTop: '6px' }}>
                  <span>Attendance Gap: {inst.attendance_gap_pct.toFixed(0)}%</span>
                  <span>Camera: {inst.camera_uptime_pct.toFixed(0)}%</span>
                  <span>Last: {formatDate(inst.last_inspected)}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
