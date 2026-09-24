import React, { useState } from 'react';
import { CctvAnalysisResult } from '../types';
import { fetchCctvMock, analyzeCctvVideo } from '../api/client';

export const CctvSection: React.FC = () => {
  const [result, setResult] = useState<CctvAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunMock = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCctvMock();
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve CCTV telemetry');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    try {
      const data = await analyzeCctvVideo(file);
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to process CCTV video');
    } finally {
      setLoading(false);
    }
  };

  // Render SVG timeline chart
  const renderTimelineChart = () => {
    if (!result || result.occupancy_timeline.length === 0) return null;

    const timeline = result.occupancy_timeline;
    const maxCount = Math.max(...timeline.map((t) => t.count), 10);
    const yMax = Math.ceil((maxCount * 1.2) / 5) * 5;
    const chartHeight = 160;
    const chartWidth = 720;
    const paddingLeft = 36;
    const paddingBottom = 26;
    const paddingTop = 12;
    const paddingRight = 16;

    const innerWidth = chartWidth - paddingLeft - paddingRight;
    const innerHeight = chartHeight - paddingTop - paddingBottom;

    const getX = (sec: number) => paddingLeft + (sec / (timeline.length - 1)) * innerWidth;
    const getY = (val: number) => paddingTop + innerHeight - (val / yMax) * innerHeight;

    const points = timeline.map((p) => `${getX(p.second)},${getY(p.count)}`).join(' ');

    return (
      <div style={{ marginTop: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>
            Second-by-Second Classroom Headcount Timeline
          </span>
          <span style={{
            fontSize: '0.75rem',
            padding: '2px 8px',
            borderRadius: 'var(--radius-xs)',
            backgroundColor: result.is_mock ? 'var(--surface-subtle)' : 'var(--accent-subtle)',
            color: result.is_mock ? 'var(--text-secondary)' : 'var(--accent)',
            border: '1px solid var(--border)',
          }}>
            {result.is_mock ? 'Deterministic Benchmark Telemetry' : 'Live YOLOv8 Person Detection'}
          </span>
        </div>

        <div style={{ width: '100%', overflowX: 'auto' }}>
          <svg
            viewBox={`0 0 ${chartWidth} ${chartHeight}`}
            style={{ width: '100%', height: 'auto', display: 'block', backgroundColor: 'var(--surface-raised)', borderRadius: 'var(--radius-sm)' }}
            aria-label="CCTV occupancy curve"
            role="img"
          >
            {/* Grid Lines */}
            {[0, 0.5, 1].map((r, i) => {
              const y = paddingTop + innerHeight * r;
              const label = Math.round(yMax * (1 - r));
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
                    {label}
                  </text>
                </g>
              );
            })}

            {/* Filled area */}
            <polygon
              points={`${points} ${getX(timeline[timeline.length - 1].second)},${paddingTop + innerHeight} ${getX(0)},${paddingTop + innerHeight}`}
              fill="var(--accent-subtle)"
              opacity="0.6"
            />

            {/* Polyline */}
            <polyline
              points={points}
              fill="none"
              stroke="var(--accent)"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Markers */}
            {timeline.filter((_, idx) => idx % 5 === 0 || idx === timeline.length - 1).map((p, idx) => (
              <g key={idx}>
                <circle cx={getX(p.second)} cy={getY(p.count)} r="3" fill="var(--accent)" />
                <text
                  x={getX(p.second)}
                  y={chartHeight - 8}
                  textAnchor="middle"
                  fontSize="9"
                  fill="var(--text-secondary)"
                >
                  {p.second}s
                </text>
              </g>
            ))}
          </svg>
        </div>
      </div>
    );
  };

  return (
    <section style={{ padding: '24px 0 40px 0' }}>
      <div className="card" style={{ padding: '28px' }}>
        <div style={{ maxWidth: '640px', marginBottom: '20px' }}>
          <h2 style={{ fontSize: '1.4rem' }}>
            Automated Vision Telemetry
          </h2>
          <p style={{ fontSize: '0.88rem', marginTop: '6px' }}>
            Upload classroom surveillance feeds or launch our deterministic benchmark telemetry.
            The vision model samples frames at regular intervals, detects verified human occupancies, and feeds physical headcount curves directly into our attendance discrepancy engine.
          </p>
        </div>

        {/* Trigger Bar */}
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: '12px',
          padding: '16px',
          backgroundColor: 'var(--surface-raised)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border)',
        }}>
          <button
            className="btn btn-primary"
            onClick={handleRunMock}
            disabled={loading}
          >
            {loading ? 'Processing Frames...' : 'Run Benchmark Telemetry'}
          </button>

          <span style={{ fontSize: '0.84rem', color: 'var(--text-tertiary)' }}>or</span>

          <label
            className="btn btn-secondary"
            style={{ cursor: loading ? 'not-allowed' : 'pointer' }}
          >
            <span>Upload CCTV Clip (.mp4, .avi)</span>
            <input
              type="file"
              accept=".mp4,.avi,.mov,.mkv"
              onChange={handleFileUpload}
              disabled={loading}
              style={{ display: 'none' }}
            />
          </label>
        </div>

        {error && (
          <div style={{
            marginTop: '16px',
            padding: '10px 14px',
            backgroundColor: 'var(--risk-high-bg)',
            color: 'var(--risk-high-text)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--risk-high-border)',
            fontSize: '0.84rem',
          }}>
            {error}
          </div>
        )}

        {/* Results Overview */}
        {result && (
          <div style={{ marginTop: '24px' }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '16px',
            }}>
              <div style={{ padding: '14px', backgroundColor: 'var(--surface-raised)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
                  Peak Occupancy
                </div>
                <div style={{ fontSize: '1.4rem', fontWeight: 600, marginTop: '2px', color: 'var(--text-primary)' }}>
                  {result.peak_occupancy} attendees
                </div>
              </div>

              <div style={{ padding: '14px', backgroundColor: 'var(--surface-raised)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
                  Average Headcount
                </div>
                <div style={{ fontSize: '1.4rem', fontWeight: 600, marginTop: '2px', color: 'var(--text-primary)' }}>
                  {result.avg_occupancy.toFixed(1)} attendees
                </div>
              </div>

              <div style={{ padding: '14px', backgroundColor: 'var(--surface-raised)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
                  Frames Evaluated
                </div>
                <div style={{ fontSize: '1.4rem', fontWeight: 600, marginTop: '2px', color: 'var(--text-primary)' }}>
                  {result.frames_analyzed} frames
                </div>
              </div>
            </div>

            {renderTimelineChart()}
          </div>
        )}
      </div>
    </section>
  );
};
