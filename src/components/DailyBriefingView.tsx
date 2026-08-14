import React, { useState, useMemo } from 'react';
import { AIIncident, formatFinancialDamage } from '../types/incident';
import { Calendar, FileText, ShieldAlert, DollarSign, Globe, Award, TrendingUp, ChevronLeft, ChevronRight, Copy, Check } from 'lucide-react';

interface DailyBriefingViewProps {
  incidents: AIIncident[];
  onSelectIncident: (incident: AIIncident) => void;
}

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

  // Incidents for selected date
  const dailyIncidents = useMemo(() => {
    return incidents.filter((inc) => inc.date === selectedDate);
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

  // Copy Executive Briefing to Clipboard
  const handleCopyBriefing = () => {
    const summaryText = `DAILY AI INCIDENT INTELLIGENCE BRIEFING (${selectedDate})\n` +
      `Total Incidents Tracked: ${dailyIncidents.length}\n` +
      `Critical Severity Events: ${criticalCount}\n` +
      `Estimated Financial Impact: ${formatFinancialDamage(totalDamageUSD)} USD\n` +
      `Impacted Entities: ${topEntities.join(', ') || 'N/A'}\n\n` +
      `KEY RISK DRIVERS & EVENTS:\n` +
      dailyIncidents.map((inc, i) => `${i + 1}. [${inc.severity.toUpperCase()}] ${inc.title}: ${inc.summary}`).join('\n\n');

    navigator.clipboard.writeText(summaryText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Date Switcher Bar with Stepper Buttons */}
      <div className="detail-section" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <FileText size={22} style={{ color: 'var(--accent-purple)' }} />
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Daily AI Incident Intelligence Briefing</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Synthesized executive summary and key risk metrics for safety analysts & regulators.
            </p>
          </div>
        </div>

        {/* Date Stepper Controls */}
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

          {/* Copy Briefing Button */}
          <button
            onClick={handleCopyBriefing}
            className="button button-primary"
            style={{ marginLeft: '0.5rem', fontSize: '0.8rem', padding: '0.4rem 0.75rem', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
            {copied ? 'Copied to Clipboard!' : 'Copy Executive Briefing'}
          </button>
        </div>
      </div>

      {/* Daily Metrics Summary Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div className="detail-section">
          <h4>Total Incidents ({selectedDate})</h4>
          <p style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>{dailyIncidents.length}</p>
        </div>
        <div className="detail-section">
          <h4>Daily Financial Impact</h4>
          <p style={{ fontSize: '2rem', fontWeight: 700, color: '#34d399' }}>
            {formatFinancialDamage(totalDamageUSD)}
          </p>
        </div>
        <div className="detail-section">
          <h4>Critical Severity Events</h4>
          <p style={{ fontSize: '2rem', fontWeight: 700, color: criticalCount > 0 ? '#ef4444' : 'var(--text-muted)' }}>
            {criticalCount}
          </p>
        </div>
        <div className="detail-section">
          <h4>Primary Entities Impacted</h4>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-main)', marginTop: '0.5rem', fontWeight: 500 }}>
            {topEntities.length > 0 ? topEntities.join(', ') : 'N/A'}
          </p>
        </div>
      </div>

      {/* Synthesized Briefing Text Card */}
      <div className="detail-section" style={{ background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.9) 100%)', borderLeft: '4px solid var(--accent-purple)', padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Award size={18} style={{ color: 'var(--accent-purple)' }} />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Executive Intelligence Synthesis — {selectedDate}</h3>
          </div>
        </div>

        {dailyIncidents.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No AI incidents recorded for {selectedDate}. All monitored systems operating normally.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.925rem', color: 'var(--text-main)', lineHeight: 1.6 }}>
            <p>
              On <strong>{selectedDate}</strong>, the Global AI Incident Monitor tracked <strong>{dailyIncidents.length} AI safety and regulatory events</strong> across monitored channels.
              {totalDamageUSD > 0 && ` Total estimated financial losses, settlements, and regulatory fines for the day amounted to approximately ${formatFinancialDamage(totalDamageUSD)} USD.`}
            </p>

            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <h4 style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <TrendingUp size={14} /> Key Risk Drivers & Root Causes
              </h4>
              <ul style={{ paddingLeft: '1.25rem', margin: 0 }}>
                {dailyIncidents.map((inc) => (
                  <li key={inc.incident_id} style={{ marginBottom: '0.35rem' }}>
                    <strong>{inc.title}:</strong> {inc.failure_mode || inc.summary}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Incident List Grid for Selected Date */}
      <div className="detail-section">
        <h3 style={{ fontSize: '1rem', marginBottom: '1rem' }}>Detailed Events for {selectedDate} ({dailyIncidents.length})</h3>

        {dailyIncidents.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No events logged on this date.</p>
        ) : (
          <div className="grid-cards">
            {dailyIncidents.map((inc) => (
              <div key={inc.incident_id} className={`incident-card card-${inc.severity}`} onClick={() => onSelectIncident(inc)}>
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
                  {inc.natsec_impact && (
                    <span className="badge" style={{ backgroundColor: 'rgba(239, 68, 68, 0.25)', color: '#fca5a5', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                      <ShieldAlert size={12} /> NatSec
                    </span>
                  )}
                </div>

                <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: '0.5rem 0', color: 'var(--text-main)' }}>{inc.title}</h3>
                <p className="card-summary">{inc.summary}</p>

                <div className="card-footer">
                  <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <span>📅 {inc.date}</span>
                    {inc.geographic_scope && inc.geographic_scope.length > 0 && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                        <Globe size={11} /> {inc.geographic_scope.slice(0, 2).join(', ')}
                      </span>
                    )}
                  </div>
                  <span className="details-link" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                    Details <ChevronRight size={14} />
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
