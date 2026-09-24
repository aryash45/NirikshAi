import React, { useState, useEffect } from 'react';
import { InstitutionDetail, InspectionCreate, InspectionResponse } from '../types';
import { submitInspection } from '../api/client';

interface InspectionModalProps {
  institution: InstitutionDetail;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (response: InspectionResponse) => void;
}

export const InspectionModal: React.FC<InspectionModalProps> = ({
  institution,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [inspectorName, setInspectorName] = useState('SIH Audit Officer (Field)');
  const [inspectionDate, setInspectionDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [beneficiaryPresent, setBeneficiaryPresent] = useState(false);
  const [staffPresent, setStaffPresent] = useState(true);
  const [infrastructureOk, setInfrastructureOk] = useState(true);
  const [cctvFunctional, setCctvFunctional] = useState(false);
  const [documentsAvailable, setDocumentsAvailable] = useState(false);
  const [severity, setSeverity] = useState<'MINOR' | 'MAJOR' | 'CRITICAL'>('CRITICAL');
  const [observations, setObservations] = useState(
    'Discrepancy confirmed during physical visit. Physical headcount was substantially lower than register logs. Camera feed was disconnected.'
  );

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const payload: InspectionCreate = {
      institution_id: institution.id,
      inspector_name: inspectorName,
      date: inspectionDate,
      findings: {
        beneficiary_present: beneficiaryPresent,
        staff_present: staffPresent,
        infrastructure_ok: infrastructureOk,
        cctv_functional: cctvFunctional,
        documents_available: documentsAvailable,
      },
      observations,
      severity,
    };

    try {
      const result = await submitInspection(payload);
      onSuccess(result);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Inspection submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.45)',
        backdropFilter: 'blur(4px)',
        WebkitBackdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        zIndex: 1000,
      }}
    >
      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: '560px',
          maxHeight: '90vh',
          overflowY: 'auto',
          backgroundColor: 'var(--surface)',
          padding: '24px',
          boxShadow: 'var(--shadow-modal)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
          <div>
            <h2 id="modal-title" style={{ fontSize: '1.25rem' }}>
              Submit Inspection Findings
            </h2>
            <p style={{ fontSize: '0.82rem', marginTop: '2px' }}>
              Recording official verification for <strong>{institution.name}</strong>.
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.2rem',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              padding: '4px 8px',
            }}
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {error && (
          <div style={{
            padding: '10px 12px',
            backgroundColor: 'var(--risk-high-bg)',
            color: 'var(--risk-high-text)',
            border: '1px solid var(--risk-high-border)',
            borderRadius: 'var(--radius-sm)',
            marginBottom: '16px',
            fontSize: '0.85rem',
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 500, marginBottom: '4px' }}>
                Inspector Full Name
              </label>
              <input
                type="text"
                required
                value={inspectorName}
                onChange={(e) => setInspectorName(e.target.value)}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 500, marginBottom: '4px' }}>
                Inspection Date
              </label>
              <input
                type="date"
                required
                value={inspectionDate}
                onChange={(e) => setInspectionDate(e.target.value)}
              />
            </div>
          </div>

          {/* Verification Findings Checklist */}
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 500, marginBottom: '8px' }}>
              Physical Verification Checklist
            </label>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              backgroundColor: 'var(--surface-raised)',
              padding: '12px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border)',
            }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.85rem' }}>
                <input
                  type="checkbox"
                  checked={beneficiaryPresent}
                  onChange={(e) => setBeneficiaryPresent(e.target.checked)}
                />
                Beneficiaries / Trainees present on site as reported
              </label>

              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.85rem' }}>
                <input
                  type="checkbox"
                  checked={staffPresent}
                  onChange={(e) => setStaffPresent(e.target.checked)}
                />
                Authorized instructional staff present
              </label>

              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.85rem' }}>
                <input
                  type="checkbox"
                  checked={infrastructureOk}
                  onChange={(e) => setInfrastructureOk(e.target.checked)}
                />
                Classroom and lab infrastructure adequate
              </label>

              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.85rem' }}>
                <input
                  type="checkbox"
                  checked={cctvFunctional}
                  onChange={(e) => setCctvFunctional(e.target.checked)}
                />
                CCTV camera hardware online and functioning
              </label>

              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.85rem' }}>
                <input
                  type="checkbox"
                  checked={documentsAvailable}
                  onChange={(e) => setDocumentsAvailable(e.target.checked)}
                />
                Physical attendance and compliance files available
              </label>
            </div>
          </div>

          {/* Severity */}
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 500, marginBottom: '4px' }}>
              Violation Severity Level
            </label>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value as 'MINOR' | 'MAJOR' | 'CRITICAL')}
            >
              <option value="MINOR">MINOR (Minor clerical or setup delays)</option>
              <option value="MAJOR">MAJOR (Multiple missing attendees or camera downtime)</option>
              <option value="CRITICAL">CRITICAL (Systematic inflation / ghost attendance)</option>
            </select>
          </div>

          {/* Observations */}
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 500, marginBottom: '4px' }}>
              Inspector Field Observations
            </label>
            <textarea
              rows={3}
              required
              value={observations}
              onChange={(e) => setObservations(e.target.value)}
            />
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? 'Updating Signals...' : 'Confirm and Recalculate Risk'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
