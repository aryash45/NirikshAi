import React from 'react';

interface NavbarProps {
  onOpenLegal: () => void;
  activeTab: 'console' | 'cctv' | 'field-inspector';
  onSelectTab: (tab: 'console' | 'cctv' | 'field-inspector') => void;
  isBackendConnected: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  onOpenLegal,
  activeTab,
  onSelectTab,
  isBackendConnected,
}) => {
  return (
    <header style={{
      backgroundColor: 'rgba(255, 255, 255, 0.88)',
      backdropFilter: 'saturate(180%) blur(20px)',
      WebkitBackdropFilter: 'saturate(180%) blur(20px)',
      borderBottom: '1px solid var(--border)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      <div className="container" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '56px',
      }}>
        {/* Brand & Identity */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: 'var(--radius-xs)',
            backgroundColor: 'var(--text-primary)',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 700,
            fontSize: '13px',
            letterSpacing: '0.04em',
          }}>
            N
          </div>
          <div>
            <span style={{ fontWeight: 600, fontSize: '0.96rem', letterSpacing: '-0.01em', color: 'var(--text-primary)' }}>
              NirikshAi
            </span>
            <span style={{
              marginLeft: '8px',
              fontSize: '0.78rem',
              color: 'var(--text-tertiary)',
              borderLeft: '1px solid var(--border)',
              paddingLeft: '8px',
            }}>
              SIH 2026 Audit Platform
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <button
            onClick={() => onSelectTab('console')}
            style={{
              background: 'none',
              border: 'none',
              padding: '6px 12px',
              fontSize: '0.88rem',
              fontWeight: activeTab === 'console' ? 600 : 400,
              color: activeTab === 'console' ? 'var(--text-primary)' : 'var(--text-secondary)',
              borderBottom: activeTab === 'console' ? '2px solid var(--accent)' : '2px solid transparent',
              cursor: 'pointer',
              transition: 'color var(--transition-fast)',
            }}
          >
            Institutions Directory
          </button>
          <button
            onClick={() => onSelectTab('cctv')}
            style={{
              background: 'none',
              border: 'none',
              padding: '6px 12px',
              fontSize: '0.88rem',
              fontWeight: activeTab === 'cctv' ? 600 : 400,
              color: activeTab === 'cctv' ? 'var(--text-primary)' : 'var(--text-secondary)',
              borderBottom: activeTab === 'cctv' ? '2px solid var(--accent)' : '2px solid transparent',
              cursor: 'pointer',
              transition: 'color var(--transition-fast)',
            }}
          >
            CCTV Verification
          </button>
          <button
            onClick={() => onSelectTab('field-inspector')}
            style={{
              background: 'none',
              border: 'none',
              padding: '6px 12px',
              fontSize: '0.88rem',
              fontWeight: activeTab === 'field-inspector' ? 600 : 400,
              color: activeTab === 'field-inspector' ? 'var(--text-primary)' : 'var(--text-secondary)',
              borderBottom: activeTab === 'field-inspector' ? '2px solid var(--accent)' : '2px solid transparent',
              cursor: 'pointer',
              transition: 'color var(--transition-fast)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>📱 Field Inspector App</span>
            <span style={{
              fontSize: '0.68rem',
              padding: '1px 5px',
              borderRadius: 'var(--radius-xs)',
              backgroundColor: 'var(--accent-subtle)',
              color: 'var(--accent)',
              fontWeight: 600,
            }}>
              PWA Mode
            </span>
          </button>
        </nav>

        {/* System Telemetry & Legal Links */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.8rem',
            color: isBackendConnected ? 'var(--risk-low-text)' : 'var(--risk-high-text)',
            backgroundColor: isBackendConnected ? 'var(--risk-low-bg)' : 'var(--risk-high-bg)',
            padding: '3px 8px',
            borderRadius: 'var(--radius-xs)',
            border: `1px solid ${isBackendConnected ? 'var(--risk-low-border)' : 'var(--risk-high-border)'}`,
          }}>
            <span style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: isBackendConnected ? 'var(--risk-low-text)' : 'var(--risk-high-text)',
            }} />
            {isBackendConnected ? 'Engine Online' : 'Connecting to API'}
          </div>

          <button
            onClick={onOpenLegal}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-tertiary)',
              fontSize: '0.82rem',
              cursor: 'pointer',
              textDecoration: 'underline',
              padding: '4px',
            }}
          >
            Privacy & Governance
          </button>
        </div>
      </div>
    </header>
  );
};
