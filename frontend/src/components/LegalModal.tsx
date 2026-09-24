import React, { useEffect } from 'react';

interface LegalModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const LegalModal: React.FC<LegalModalProps> = ({ isOpen, onClose }) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="legal-title"
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
          maxWidth: '620px',
          maxHeight: '85vh',
          overflowY: 'auto',
          backgroundColor: 'var(--surface)',
          padding: '28px',
          boxShadow: 'var(--shadow-modal)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
          <div>
            <h2 id="legal-title" style={{ fontSize: '1.25rem' }}>
              Data Governance & Privacy Policy
            </h2>
            <div style={{
              display: 'inline-block',
              marginTop: '4px',
              padding: '2px 8px',
              borderRadius: 'var(--radius-xs)',
              backgroundColor: 'var(--accent-subtle)',
              color: 'var(--accent)',
              fontSize: '0.74rem',
              fontWeight: 600,
            }}>
              Draft Specification for Review
            </div>
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

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          <section>
            <h3 style={{ fontSize: '0.92rem', color: 'var(--text-primary)', marginBottom: '4px' }}>
              1. Video Surveillance and Headcount Processing
            </h3>
            <p>
              Classroom CCTV streams and uploaded video files are evaluated on-device or within sandboxed container instances solely for human presence detection (headcount counting). Raw video frames are discarded immediately after frame sampling. The system does not extract, retain, or index facial recognition biometrics or personally identifiable video profiles.
            </p>
          </section>

          <section>
            <h3 style={{ fontSize: '0.92rem', color: 'var(--text-primary)', marginBottom: '4px' }}>
              2. Digital Personal Data Protection (DPDP) Alignment
            </h3>
            <p>
              This platform processes aggregated institutional metadata and non-sensitive attendance counters. All evaluation scores represent algorithmic statistical models based on verifiable public signals (camera uptime, registered batch sizes, inspection findings, and filing timestamps).
            </p>
          </section>

          <section>
            <h3 style={{ fontSize: '0.92rem', color: 'var(--text-primary)', marginBottom: '4px' }}>
              3. Inspection Audit Records & Immutability
            </h3>
            <p>
              Field inspection logs recorded through this portal establish formal administrative review records. Findings and associated risk score recalculations are time-stamped and preserved for subsequent ministerial review.
            </p>
          </section>

          <section>
            <h3 style={{ fontSize: '0.92rem', color: 'var(--text-primary)', marginBottom: '4px' }}>
              4. Demonstration Sandbox Notice
            </h3>
            <p>
              Telemetry data displayed within this Smart India Hackathon prototype environment incorporates simulated institution names and benchmark records for verification of algorithmic logic and user flows.
            </p>
          </section>
        </div>

        <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
