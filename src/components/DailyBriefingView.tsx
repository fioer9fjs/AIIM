import React, { useState, useMemo } from 'react';
import { AIIncident, formatFinancialDamage } from '../types/incident';
import { Calendar, FileText, ShieldAlert, DollarSign, Globe, Award, TrendingUp, Copy, Check, AlertCircle } from 'lucide-react';

import { deduplicateIncidents } from '../App';

interface DailyBriefingViewProps {
  incidents: AIIncident[];
  dateRange?: [string, string];
  onSelectIncident: (incident: AIIncident) => void;
}

const SEVERITY_RANK: Record<string, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1
};

export const DailyBriefingView: React.FC<DailyBriefingViewProps> = ({ incidents, dateRange, onSelectIncident }) => {
  const [copied, setCopied] = useState<boolean>(false);

  // Incidents for active filter window, DEDUPLICATED AND SORTED BY CRITICALITY DESCENDING
  const dailyIncidents = useMemo(() => {
    const dedupped = deduplicateIncidents(incidents);
    return dedupped.sort((a, b) => (SEVERITY_RANK[b.severity] || 0) - (SEVERITY_RANK[a.severity] || 0));
  }, [incidents]);

  // Statistics
  const criticalCount = useMemo(() => {
    return dailyIncidents.filter((i) => i.severity === 'critical').length;
  }, [dailyIncidents]);

  const totalDamageUSD = useMemo(() => {
    return dailyIncidents.reduce((sum, inc) => sum + (inc.financial_damage_usd || 0), 0);
  }, [dailyIncidents]);

  const affectedOrgs = useMemo(() => {
    const orgs = new Set<string>();
    dailyIncidents.forEach((inc) => {
      (inc.affected_parties || []).forEach((p) => orgs.add(p));
    });
    return orgs.size;
  }, [dailyIncidents]);

  const primaryHarmDomain = useMemo(() => {
    const counts: Record<string, number> = {};
    dailyIncidents.forEach((inc) => {
      const domain = (inc as any).taxonomy?.harm_domain || inc.harm_domain || 'general';
      counts[domain] = (counts[domain] || 0) + 1;
    });
    let topDomain = 'N/A';
    let max = 0;
    Object.entries(counts).forEach(([d, count]) => {
      if (count > max) {
        max = count;
        topDomain = d.replace(/_/g, ' ');
      }
    });
    return topDomain;
  }, [dailyIncidents]);

  // Date range label
  const isSingleDay = !dateRange || dateRange[0] === dateRange[1];
  const dateText = isSingleDay
    ? (dateRange ? dateRange[0] : (dailyIncidents[0]?.date || 'Today'))
    : `${dateRange[0]} to ${dateRange[1]}`;

  // Copy Executive Briefing Text to Clipboard
  const handleCopyBriefing = () => {
    let text = `Executive Intelligence Synthesis — ${dateText}\n`;
    text += `On ${dateText}, the Global AI Incident Monitor tracked ${dailyIncidents.length} AI Incidents across international channels.\n\n`;
    text += `Key Risk Drivers (Sorted by Criticality)\n`;

    dailyIncidents.forEach((inc) => {
      const damageStr = (inc.financial_damage_usd || 0) > 0 ? `$${inc.financial_damage_usd?.toLocaleString()} USD` : 'N/A';
      text += `${inc.severity.toUpperCase()} — ${inc.title}: ${inc.summary} (Est. Financial Impact: ${damageStr})\n`;
    });

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Top Editorial Banner */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <FileText size={28} style={{ color: 'var(--accent-purple)' }} />
          <div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Executive Intelligence Synthesis — {dateText}
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Synthesized intelligence briefing sorted by criticality with embedded financial impact estimations.
            </p>
          </div>
        </div>

        {/* Copy Export Button */}
        <button
          onClick={handleCopyBriefing}
          className="button button-primary"
          style={{ fontSize: '0.8rem', padding: '0.4rem 0.75rem', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
        >
          {copied ? <Check size={14} /> : <Copy size={14} />}
          {copied ? 'Copied Briefing!' : 'Copy Executive Briefing'}
        </button>
      </div>

      {/* 2-COLUMN EDITORIAL LAYOUT */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 340px', gap: '1.5rem', alignItems: 'start' }}>
        
        {/* LEFT COLUMN: Executive Briefing Column (Optimal Typographic Measure max-width: 68ch) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
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
              <Calendar size={18} style={{ color: 'var(--accent-purple)' }} />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-main)' }}>
                Daily AI Safety & Incident Report
              </h3>
            </div>

            {dailyIncidents.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
                No AI incidents recorded for {dateText}. All monitored systems operating within nominal baseline parameters.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', maxWidth: '68ch', fontSize: '1.025rem', color: '#e2e8f0', lineHeight: 1.75 }}>
                <p>
                  On <strong>{dateText}</strong>, the Global AI Incident Monitor tracked <strong>{dailyIncidents.length} AI Incidents</strong> across international channels.
                  {totalDamageUSD > 0 && ` Total cumulative estimated financial impact for the period reached ${formatFinancialDamage(totalDamageUSD)} USD.`}
                </p>

                {/* Risk Breakdown Box (Sorted by Criticality & Damage in Parentheses) */}
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1.25rem', borderRadius: '8px', border: '1px solid var(--border-color)', margin: '0.5rem 0' }}>
                  <h4 style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <ShieldAlert size={14} /> Key Risk Drivers (Sorted by Criticality)
                  </h4>
                  <ul style={{ paddingLeft: '1.25rem', margin: 0, display: 'flex', flexDirection: 'column', gap: '0.85rem', fontSize: '0.925rem' }}>
                    {dailyIncidents.map((inc) => (
                      <li key={inc.incident_id} style={{ cursor: 'pointer' }} onClick={() => onSelectIncident(inc)}>
                        <span className={`severity-badge severity-${inc.severity}`} style={{ fontSize: '0.7rem', padding: '0.1rem 0.4rem', marginRight: '0.4rem', textTransform: 'uppercase', fontWeight: 700 }}>
                          {inc.severity}
                        </span>
                        <strong style={{ color: 'var(--text-main)' }}>{inc.title}</strong>: {inc.summary}{' '}
                        <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>
                          (Est. Financial Impact: {formatFinancialDamage(inc.financial_damage_usd)})
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>

                <p style={{ fontSize: '0.925rem', color: 'var(--text-muted)', fontStyle: 'italic', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '1rem' }}>
                  * All incident reports are automatically ingested via multi-source harvesting and categorized using CSET & EU AI Act risk taxonomies.
                </p>
              </div>
            )}
          </article>

          {/* Detailed Incident Cards List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertCircle size={18} style={{ color: 'var(--accent-cyan)' }} />
              Detailed Incident Reports ({dailyIncidents.length})
            </h3>

            {dailyIncidents.map((inc) => (
              <div
                key={inc.incident_id}
                className="incident-card"
                onClick={() => onSelectIncident(inc)}
                style={{ cursor: 'pointer', transition: 'all 0.2s ease' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', marginBottom: '0.5rem' }}>
                  <span className={`severity-badge severity-${inc.severity}`}>
                    {inc.severity}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                    ID: {inc.incident_id} • {inc.date}
                  </span>
                </div>

                <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.4rem' }}>
                  {inc.title}
                </h4>

                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.75rem', lineHeight: 1.5 }}>
                  {inc.summary}
                </p>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>
                    Est. Financial Impact: {formatFinancialDamage(inc.financial_damage_usd)}
                  </span>
                  {inc.source_urls && inc.source_urls.length > 0 && (
                    <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>
                      {inc.source_urls.length} Verified Source{inc.source_urls.length > 1 ? 's' : ''}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

        </div>

        {/* RIGHT SIDEBAR: Daily Aggregated Metrics Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', position: 'sticky', top: '5rem' }}>
          
          <div className="detail-section">
            <h4 style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>
              Daily Incident Metrics
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Total Incidents:</span>
                <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>{dailyIncidents.length}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Critical Incidents:</span>
                <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-red)' }}>{criticalCount}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Affected Entities:</span>
                <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-blue)' }}>{affectedOrgs}</span>
              </div>
            </div>
          </div>

          {/* Financial Impact Card */}
          <div className="detail-section" style={{ background: 'rgba(52, 211, 153, 0.08)', borderColor: 'rgba(52, 211, 153, 0.25)' }}>
            <h4 style={{ fontSize: '0.75rem', color: '#34d399', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <DollarSign size={14} /> Cumulative Financial Impact
            </h4>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#34d399', marginBottom: '0.2rem' }}>
              {formatFinancialDamage(totalDamageUSD)}
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Estimated economic damage including regulatory fines, class action losses, and statistical life valuations.
            </p>
          </div>

          {/* Dominant Risk Focus */}
          <div className="detail-section">
            <h4 style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <TrendingUp size={14} style={{ color: 'var(--accent-cyan)' }} /> Primary Harm Domain
            </h4>
            <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--accent-cyan)', textTransform: 'capitalize' }}>
              {primaryHarmDomain}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};
