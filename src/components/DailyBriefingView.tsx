import React, { useState, useMemo } from 'react';
import { AIIncident, formatFinancialDamage } from '../types/incident';
import { Calendar, FileText, ShieldAlert, DollarSign, Globe, Award, TrendingUp, ChevronLeft, ChevronRight, Copy, Check, AlertCircle } from 'lucide-react';

interface DailyBriefingViewProps {
  incidents: AIIncident[];
  onSelectIncident: (incident: AIIncident) => void;
}

const SEVERITY_RANK: Record<string, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1
};

export const DailyBriefingView: React.FC<DailyBriefingViewProps> = ({ incidents, onSelectIncident }) => {
  // Extract unique dates sorted descending
  const availableDates = useMemo(() => {
    const datesSet = new Set<string>();
    incidents.forEach((inc) => {
      if (inc.date) datesSet.add(inc.date);
    });
    const sorted = Array.from(datesSet).sort((a, b) => b.localeCompare(a));
    return sorted.length > 0 ? sorted : [new Date().toISOString().split('T')[0]];
  }, [incidents]);

  const [selectedDate, setSelectedDate] = useState<string>(availableDates[0] || '');
  const [copied, setCopied] = useState<boolean>(false);

  const currentIndex = availableDates.indexOf(selectedDate);

  const handlePrevDate = () => {
    if (currentIndex < availableDates.length - 1) {
      setSelectedDate(availableDates[currentIndex + 1]);
    }
  };

  const handleNextDate = () => {
    if (currentIndex > 0) {
      setSelectedDate(availableDates[currentIndex - 1]);
    }
  };

  // Incidents for selected date, SORTED BY CRITICALITY DESCENDING
  const dailyIncidents = useMemo(() => {
    const list = incidents.filter((inc) => inc.date === selectedDate);
    return list.sort((a, b) => (SEVERITY_RANK[b.severity] || 0) - (SEVERITY_RANK[a.severity] || 0));
  }, [incidents, selectedDate]);

  // Daily statistics
  const criticalCount = useMemo(() => {
    return dailyIncidents.filter((i) => i.severity === 'critical').length;
  }, [dailyIncidents]);

  const totalDamageUSD = useMemo(() => {
    return dailyIncidents.reduce((sum, inc) => sum + (inc.financial_damage_usd || 0), 0);
  }, [dailyIncidents]);

  const topEntities = useMemo(() => {
    const set = new Set<string>();
    dailyIncidents.forEach((inc) => {
      if (inc.affected_parties) inc.affected_parties.forEach((p) => set.add(p));
    });
    return Array.from(set).slice(0, 5);
  }, [dailyIncidents]);

  // Copy Executive Briefing to Clipboard (with damage in parentheses)
  const handleCopyBriefing = () => {
    const summaryText = `DAILY AI INCIDENT INTELLIGENCE BRIEFING (${selectedDate})\n` +
      `Total Incidents Tracked: ${dailyIncidents.length}\n` +
      `Critical Severity Events: ${criticalCount}\n` +
      `Estimated Financial Impact: ${formatFinancialDamage(totalDamageUSD)} USD\n` +
      `Impacted Entities: ${topEntities.join(', ') || 'N/A'}\n\n` +
      `KEY RISK DRIVERS & EVENTS (SORTED BY CRITICALITY):\n` +
      dailyIncidents.map((inc, i) => `${i + 1}. [${inc.severity.toUpperCase()}] ${inc.title}: ${inc.summary} (Est. Financial Impact: ${formatFinancialDamage(inc.financial_damage_usd)})`).join('\n\n');

    navigator.clipboard.writeText(summaryText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Top Header Controls Bar */}
      <div className="detail-section" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <FileText size={22} style={{ color: 'var(--accent-purple)' }} />
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Daily Executive AI Risk Briefing</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Synthesized intelligence briefing sorted by criticality with embedded financial impact estimations.
            </p>
          </div>
        </div>

        {/* Date Stepper Controls & Export Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button
            onClick={handlePrevDate}
            disabled={currentIndex >= availableDates.length - 1}
            className="button button-outline"
            style={{ padding: '0.35rem 0.6rem', opacity: currentIndex >= availableDates.length - 1 ? 0.4 : 1 }}
            title="Previous Day"
          >
            <ChevronLeft size={16} />
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Calendar size={15} style={{ color: 'var(--accent-cyan)' }} />
            <select
              className="filter-select"
              style={{ width: '150px', padding: '0.35rem 0.6rem', fontWeight: 600, fontSize: '0.85rem' }}
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
            >
              {availableDates.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleNextDate}
            disabled={currentIndex <= 0}
            className="button button-outline"
            style={{ padding: '0.35rem 0.6rem', opacity: currentIndex <= 0 ? 0.4 : 1 }}
            title="Next Day"
          >
            <ChevronRight size={16} />
          </button>

          <button
            onClick={handleCopyBriefing}
            className="button button-primary"
            style={{ marginLeft: '0.5rem', fontSize: '0.8rem', padding: '0.4rem 0.75rem', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
            {copied ? 'Copied Briefing!' : 'Copy Executive Briefing'}
          </button>
        </div>
      </div>

      {/* 2-COLUMN EDITORIAL LAYOUT */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 340px', gap: '1.5rem', alignItems: 'start' }}>
        
        {/* LEFT COLUMN: EDITORIAL NARRATIVE (SORTED BY CRITICALITY & WITH DAMAGE IN PARENTHESES) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Main Briefing Article Panel */}
          <article
            className="detail-section"
            style={{
              background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.85) 100%)',
              borderLeft: '4px solid var(--accent-purple)',
              padding: '2rem',
              borderRadius: '12px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
              <Award size={20} style={{ color: 'var(--accent-purple)' }} />
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)' }}>
                Executive Intelligence Synthesis — {selectedDate}
              </h2>
            </div>

            {dailyIncidents.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
                No AI incidents recorded for {selectedDate}. All monitored systems operating within nominal baseline parameters.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', maxWidth: '68ch', fontSize: '1.025rem', color: '#e2e8f0', lineHeight: 1.75 }}>
                <p>
                  On <strong>{selectedDate}</strong>, the Global AI Incident Monitor tracked <strong>{dailyIncidents.length} AI safety and regulatory events</strong> across international channels.
                  {totalDamageUSD > 0 && ` Total cumulative estimated financial impact for the day reached ${formatFinancialDamage(totalDamageUSD)} USD.`}
                </p>

                {/* Risk Breakdown Box (Sorted by Criticality & Damage in Parentheses) */}
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1.25rem', borderRadius: '8px', border: '1px solid var(--border-color)', margin: '0.5rem 0' }}>
                  <h4 style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <TrendingUp size={15} /> Key Risk Drivers (Sorted by Criticality)
                  </h4>
                  <ul style={{ paddingLeft: '1.25rem', margin: 0, display: 'flex', flexDirection: 'column', gap: '0.65rem', fontSize: '0.95rem' }}>
                    {dailyIncidents.map((inc) => (
                      <li key={inc.incident_id} style={{ lineHeight: 1.6 }}>
                        <span className={`badge badge-${inc.severity}`} style={{ marginRight: '0.4rem', fontSize: '0.65rem' }}>{inc.severity}</span>
                        <strong style={{ color: 'var(--text-main)' }}>{inc.title}:</strong>{' '}
                        <span style={{ color: 'var(--text-muted)' }}>{inc.failure_mode || inc.summary}</span>{' '}
                        <strong style={{ color: '#34d399', fontSize: '0.875rem' }}>
                          (Est. Financial Impact: {formatFinancialDamage(inc.financial_damage_usd)})
                        </strong>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </article>

          {/* Detailed Events Feed Grid (Sorted by Criticality & Damage in Parentheses) */}
          <div className="detail-section">
            <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertCircle size={16} style={{ color: 'var(--accent-cyan)' }} />
              Detailed Incident Feed for {selectedDate} ({dailyIncidents.length} Events, Sorted by Criticality)
            </h3>

            {dailyIncidents.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No logged events for this date.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {dailyIncidents.map((inc) => (
                  <div
                    key={inc.incident_id}
                    className={`incident-card card-${inc.severity}`}
                    onClick={() => onSelectIncident(inc)}
                    style={{ padding: '1rem' }}
                  >
                    <div className="card-header">
                      <span className={`badge badge-${inc.severity}`}>{inc.severity}</span>
                      <span className={`badge badge-${inc.verification_status}`}>{inc.verification_status}</span>
                      <span className="badge" style={{ backgroundColor: 'rgba(168, 85, 247, 0.2)', color: '#d8b4fe' }}>
                        Src: {(inc.source_type || 'google_news_rss').replace(/_/g, ' ')}
                      </span>
                      {inc.financial_damage_usd ? inc.financial_damage_usd > 0 ? (
                        <span className="badge" style={{ backgroundColor: 'rgba(16, 185, 129, 0.2)', color: '#34d399', display: 'inline-flex', alignItems: 'center', gap: '0.2rem', fontWeight: 700 }}>
                          <DollarSign size={12} /> {formatFinancialDamage(inc.financial_damage_usd)}
                        </span>
                      ) : null : null}
                    </div>

                    <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: '0.4rem 0', color: 'var(--text-main)' }}>{inc.title}</h3>
                    <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.6, margin: '0.4rem 0' }}>
                      {inc.summary}{' '}
                      <strong style={{ color: '#34d399' }}>
                        (Est. Financial Impact: {formatFinancialDamage(inc.financial_damage_usd)})
                      </strong>
                    </p>

                    <div className="card-footer" style={{ marginTop: '0.5rem', paddingTop: '0.5rem' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>📅 {inc.date}</span>
                      <span className="details-link" style={{ fontSize: '0.8rem' }}>View Analysis →</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT SIDEBAR: KEY METRICS & KPI SUMMARY */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', position: 'sticky', top: '5rem' }}>
          <div className="detail-section">
            <h4 style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Daily Incident Count
            </h4>
            <p style={{ fontSize: '2.25rem', fontWeight: 700, color: 'var(--accent-cyan)', margin: '0.2rem 0' }}>
              {dailyIncidents.length}
            </p>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Logged on {selectedDate}</span>
          </div>

          <div className="detail-section">
            <h4 style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Est. Financial Damage
            </h4>
            <p style={{ fontSize: '2.25rem', fontWeight: 700, color: '#34d399', margin: '0.2rem 0' }}>
              {formatFinancialDamage(totalDamageUSD)}
            </p>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Includes fines & legal liabilities</span>
          </div>

          <div className="detail-section">
            <h4 style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Critical Risk Events
            </h4>
            <p style={{ fontSize: '2.25rem', fontWeight: 700, color: criticalCount > 0 ? '#ef4444' : 'var(--text-muted)', margin: '0.2rem 0' }}>
              {criticalCount}
            </p>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>High-impact severity cases</span>
          </div>

          <div className="detail-section">
            <h4 style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>
              Primary Impacted Entities
            </h4>
            {topEntities.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                {topEntities.map((ent, idx) => (
                  <div key={idx} style={{ fontSize: '0.85rem', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{ color: 'var(--accent-purple)' }}>•</span> {ent}
                  </div>
                ))}
              </div>
            ) : (
              <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>None logged</span>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
