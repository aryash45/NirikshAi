import React, { useState, useEffect, useCallback } from 'react';
import {
  StatsSummary,
  InstitutionSummary,
  InstitutionDetail as InstitutionDetailType,
  InspectionResponse,
} from './types';
import {
  fetchStatsSummary,
  fetchInstitutions,
  fetchInstitutionDetail,
  subscribeToRiskUpdates,
} from './api/client';
import { Navbar } from './components/Navbar';
import { StatsOverview } from './components/StatsOverview';
import { InstitutionList } from './components/InstitutionList';
import { InstitutionDetail } from './components/InstitutionDetail';
import { CctvSection } from './components/CctvSection';
import { MobileFieldInspector } from './components/MobileFieldInspector';
import { LegalModal } from './components/LegalModal';

export const App: React.FC = () => {
  const [stats, setStats] = useState<StatsSummary | null>(null);
  const [institutions, setInstitutions] = useState<InstitutionSummary[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectedDetail, setSelectedDetail] = useState<InstitutionDetailType | null>(null);

  const [activeTab, setActiveTab] = useState<'console' | 'cctv' | 'field-inspector'>('console');
  const [legalOpen, setLegalOpen] = useState(false);
  const [isBackendConnected, setIsBackendConnected] = useState(false);

  const [loadingInstitutions, setLoadingInstitutions] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [recentNotification, setRecentNotification] = useState<string | null>(null);

  // Initial Data Fetching
  const loadInitialData = useCallback(async () => {
    try {
      const [statsData, instData] = await Promise.all([
        fetchStatsSummary(),
        fetchInstitutions(),
      ]);
      setStats(statsData);
      setInstitutions(instData);
      setIsBackendConnected(true);

      // Default select the first (highest risk) institution
      if (instData.length > 0 && selectedId === null) {
        setSelectedId(instData[0].id);
      }
    } catch (err) {
      console.error('Failed to load initial data', err);
      setIsBackendConnected(false);
    } finally {
      setLoadingInstitutions(false);
    }
  }, [selectedId]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Load Institution Detail on Selection
  const loadDetail = useCallback(async (id: number) => {
    setLoadingDetail(true);
    try {
      const detail = await fetchInstitutionDetail(id);
      setSelectedDetail(detail);
      setIsBackendConnected(true);
    } catch (err) {
      console.error(`Failed to load detail for institution ${id}`, err);
    } finally {
      setLoadingDetail(false);
    }
  }, []);

  useEffect(() => {
    if (selectedId !== null) {
      loadDetail(selectedId);
    }
  }, [selectedId, loadDetail]);

  // Subscribe to live WebSocket broadcasts
  useEffect(() => {
    const unsubscribe = subscribeToRiskUpdates(({ institution_id, data }) => {
      setInstitutions((prev) => {
        const next = prev.map((inst) => (inst.id === institution_id ? data : inst));
        return next.sort((a, b) => b.risk_score - a.risk_score);
      });

      if (selectedId === institution_id) {
        loadDetail(institution_id);
      }

      setRecentNotification(`Live telemetry update received for center #${institution_id}`);
      setTimeout(() => setRecentNotification(null), 5000);
    });

    return () => unsubscribe();
  }, [selectedId, loadDetail]);

  // Handle Inspection submission result
  const handleInspectionSuccess = (response: InspectionResponse) => {
    setRecentNotification(response.message);
    setTimeout(() => setRecentNotification(null), 6000);

    // Refresh stats and detail
    loadInitialData();
    if (selectedId !== null) {
      loadDetail(selectedId);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        onOpenLegal={() => setLegalOpen(true)}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        isBackendConnected={isBackendConnected}
      />

      <main style={{ flex: 1, paddingBottom: '60px' }}>
        <div className="container">
          {/* Notification Banner for Closed-Loop Inspection updates */}
          {recentNotification && (
            <div
              style={{
                marginTop: '16px',
                padding: '12px 16px',
                backgroundColor: 'var(--accent-subtle)',
                color: 'var(--accent)',
                border: '1px solid var(--accent-border)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.86rem',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span>{recentNotification}</span>
              <button
                onClick={() => setRecentNotification(null)}
                style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>
          )}

          {/* Product Headline & Positioning */}
          <section style={{ paddingTop: '28px', paddingBottom: '8px' }}>
            <h1 style={{ fontSize: '2.1rem', letterSpacing: '-0.03em', maxWidth: '780px' }}>
              Institutional monitoring powered by automated discrepancy detection.
            </h1>
            <p style={{ fontSize: '1rem', marginTop: '10px', maxWidth: '640px', color: 'var(--text-secondary)' }}>
              Cross-referencing surveillance headcount against self-reported register logs to direct field inspectors where attendance inflation is detected.
            </p>
          </section>

          {/* Telemetry Metric Cards */}
          <StatsOverview stats={stats} loading={loadingInstitutions} />

          {/* Tab Views */}
          {activeTab === 'console' && (
            <section style={{ marginTop: '12px' }}>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'minmax(300px, 380px) 1fr',
                gap: '20px',
                alignItems: 'start',
              }}>
                {/* Left Column: Directory */}
                <div>
                  <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h2 style={{ fontSize: '1.05rem' }}>Centers Directory</h2>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)' }}>
                      Ranked by Risk Score
                    </span>
                  </div>
                  <InstitutionList
                    institutions={institutions}
                    selectedId={selectedId}
                    onSelect={(id) => setSelectedId(id)}
                    loading={loadingInstitutions}
                  />
                </div>

                {/* Right Column: Deep-Dive Inspector */}
                <div>
                  <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h2 style={{ fontSize: '1.05rem' }}>Institutional Intelligence & Audit</h2>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)' }}>
                      Live Closed-Loop Feedback
                    </span>
                  </div>
                  <InstitutionDetail
                    institution={selectedDetail}
                    loading={loadingDetail}
                    onInspectionUpdated={handleInspectionSuccess}
                    onRefresh={() => selectedId && loadDetail(selectedId)}
                  />
                </div>
              </div>
            </section>
          )}

          {activeTab === 'cctv' && (
            <CctvSection />
          )}

          {activeTab === 'field-inspector' && (
            <MobileFieldInspector
              institutions={institutions}
              onInspectionCompleted={handleInspectionSuccess}
            />
          )}
        </div>
      </main>

      {/* Restrained Footer */}
      <footer style={{ borderTop: '1px solid var(--border)', backgroundColor: 'var(--surface)', padding: '24px 0' }}>
        <div className="container" style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '12px', fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>
          <div>
            <span>NirikshAi • AI Institutional Compliance Architecture</span>
            <span style={{ marginLeft: '12px' }}>Smart India Hackathon 2026</span>
          </div>
          <div style={{ display: 'flex', gap: '16px' }}>
            <button
              onClick={() => setLegalOpen(true)}
              style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', textDecoration: 'underline' }}
            >
              Privacy & DPDP Compliance
            </button>
            <span>v1.0.0</span>
          </div>
        </div>
      </footer>

      {/* Legal & Governance Modal */}
      <LegalModal isOpen={legalOpen} onClose={() => setLegalOpen(false)} />
    </div>
  );
};

export default App;
