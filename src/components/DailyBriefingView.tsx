import React, { useState, useMemo } from 'react';
import { AIIncident, formatFinancialDamage, computeFinancialImpactTotals } from '../types/incident';
import { FileText, ShieldAlert, DollarSign, TrendingUp, Copy, Check, ExternalLink, ArrowUpDown, Globe } from 'lucide-react';

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
  const [briefingSort, setBriefingSort] = useState<'criticality' | 'damage'>('criticality');
  const [showDiscrete, setShowDiscrete] = useState<boolean>(true);
  const [showMacro, setShowMacro] = useState<boolean>(true);

  // Incidents for active filter window, DEDUPLICATED AND FILTERED BY SCOPE & SORT SELECTION
  const dailyIncidents = useMemo(() => {
    const dedupped = deduplicateIncidents(incidents);
    const filtered = dedupped.filter((inc) => {
      const isMacro = inc.impact_scope === 'cumulative_macro_trend' || (inc.financial_damage_usd || 0) >= 5_000_000_000;
      if (isMacro && !showMacro) return false;
      if (!isMacro && !showDiscrete) return false;
      return true;
    });

    if (briefingSort === 'damage') {
      return filtered.sort((a, b) => (b.financial_damage_usd || 0) - (a.financial_damage_usd || 0));
    }
    return filtered.sort((a, b) => (SEVERITY_RANK[b.severity] || 0) - (SEVERITY_RANK[a.severity] || 0));
  }, [incidents, briefingSort, showDiscrete, showMacro]);

  // Statistics
  const criticalCount = useMemo(() => {
    return dailyIncidents.filter((i) => i.severity === 'critical').length;
  }, [dailyIncidents]);

  // Separated Financial Impact Totals (Discrete Events vs Macro Industry Trend)
  const { discreteTotalUSD, macroBenchmarkUSD } = useMemo(() => {
    return computeFinancialImpactTotals(dailyIncidents);
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
    text += `On ${dateText}, the Global AI Incident Monitor tracked ${dailyIncidents.length} AI Incidents across international channels.\n`;
    text += `Discrete Single-Event Damages: ${formatFinancialDamage(discreteTotalUSD)} USD\n`;
    if (macroBenchmarkUSD > 0) {
      text += `Industry Macro Trend Benchmark: ${formatFinancialDamage(macroBenchmarkUSD)} USD\n`;
    }
    text += `\nKey Risk Drivers (Sorted by ${briefingSort === 'damage' ? 'Financial Damage ($ USD)' : 'Criticality'})\n`;

    dailyIncidents.forEach((inc) => {
      const damageStr = (inc.financial_damage_usd || 0) > 0 ? `$${inc.financial_damage_usd?.toLocaleString()} USD` : 'N/A';
      const scopeLabel = inc.impact_scope === 'cumulative_macro_trend' ? '[Macro Industry Trend]' : '[Discrete Event]';
      text += `${inc.severity.toUpperCase()} — ${inc.title}: ${inc.summary} (${scopeLabel} Est. Impact: ${damageStr})\n`;
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
              Synthesized 1-page intelligence briefing with separated discrete losses and macro industry benchmarks.
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
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <ShieldAlert size={18} style={{ color: 'var(--accent-purple)' }} />
                <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-main)' }}>
                  Daily AI Safety & Incident Synthesis
                </h3>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                {/* Event Scope Filter Controls (Discrete vs Macro) */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', background: 'rgba(0,0,0,0.4)', padding: '0.2rem 0.4rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                  <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)', fontWeight: 600, paddingRight: '0.2rem' }}>Scope:</span>
                  
                  <label
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      fontSize: '0.725rem',
                      fontWeight: 600,
                      color: showDiscrete ? '#34d399' : 'var(--text-muted)',
                      background: showDiscrete ? 'rgba(52, 211, 153, 0.15)' : 'transparent',
                      padding: '0.2rem 0.45rem',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      border: showDiscrete ? '1px solid rgba(52, 211, 153, 0.3)' : '1px solid transparent',
                      userSelect: 'none',
                      transition: 'all 0.15s ease'
                    }}
                    title="Toggle Discrete Single Events"
                  >
                    <input
                      type="checkbox"
                      checked={showDiscrete}
                      onChange={(e) => {
                        const checked = e.target.checked;
                        if (!checked && !showMacro) return;
                        setShowDiscrete(checked);
                      }}
                      style={{ accentColor: '#34d399', width: '12px', height: '12px', cursor: 'pointer' }}
                    />
                    Discrete
                  </label>

                  <label
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      fontSize: '0.725rem',
                      fontWeight: 600,
                      color: showMacro ? '#c084fc' : 'var(--text-muted)',
                      background: showMacro ? 'rgba(168, 85, 247, 0.15)' : 'transparent',
                      padding: '0.2rem 0.45rem',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      border: showMacro ? '1px solid rgba(168, 85, 247, 0.3)' : '1px solid transparent',
                      userSelect: 'none',
                      transition: 'all 0.15s ease'
                    }}
                    title="Toggle Industry Macro Trend Reports"
                  >
                    <input
                      type="checkbox"
                      checked={showMacro}
                      onChange={(e) => {
                        const checked = e.target.checked;
                        if (!checked && !showDiscrete) return;
                        setShowMacro(checked);
                      }}
                      style={{ accentColor: '#a855f7', width: '12px', height: '12px', cursor: 'pointer' }}
                    />
                    Macro
                  </label>
                </div>

                {/* Sort Switcher Widget for Daily Briefing */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', background: 'rgba(0,0,0,0.4)', padding: '0.2rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                  <ArrowUpDown size={12} style={{ color: 'var(--text-muted)', marginLeft: '0.2rem' }} />
                  <button
                    onClick={() => setBriefingSort('criticality')}
                  style={{
                    border: 'none',
                    background: briefingSort === 'criticality' ? 'var(--accent-purple)' : 'transparent',
                    color: briefingSort === 'criticality' ? '#ffffff' : 'var(--text-muted)',
                    fontSize: '0.725rem',
                    padding: '0.2rem 0.5rem',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontWeight: 600
                  }}
                  title="Sort by Incident Criticality"
                >
                  Criticality
                </button>
                <button
                  onClick={() => setBriefingSort('damage')}
                  style={{
                    border: 'none',
                    background: briefingSort === 'damage' ? '#10b981' : 'transparent',
                    color: briefingSort === 'damage' ? '#ffffff' : 'var(--text-muted)',
                    fontSize: '0.725rem',
                    padding: '0.2rem 0.5rem',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontWeight: 600
                  }}
                  title="Sort by Highest Financial Impact ($ USD)"
                >
                  Financial Impact ($)
                </button>
              </div>
            </div>
          </div>

            {dailyIncidents.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
                No AI incidents recorded for {dateText}. All monitored systems operating within nominal baseline parameters.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', maxWidth: '68ch', fontSize: '1.025rem', color: '#e2e8f0', lineHeight: 1.75 }}>
                <p>
                  On <strong>{dateText}</strong>, the Global AI Incident Monitor tracked <strong>{dailyIncidents.length} AI Incidents</strong> across international channels.
                  {discreteTotalUSD > 0 && ` Total discrete single-event financial losses reached ${formatFinancialDamage(discreteTotalUSD)} USD.`}
                  {macroBenchmarkUSD > 0 && ` Additionally, industry macro threat reports documented ${formatFinancialDamage(macroBenchmarkUSD)} USD in cumulative sector losses.`}
                </p>

                {/* Risk Breakdown Box */}
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1.25rem', borderRadius: '8px', border: '1px solid var(--border-color)', margin: '0.5rem 0' }}>
                  <h4 style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)', marginBottom: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <ShieldAlert size={14} /> Key Risk Drivers (Sorted by {briefingSort === 'damage' ? 'Financial Damage' : 'Criticality'})
                  </h4>
                  <ul style={{ paddingLeft: 0, listStyle: 'none', margin: 0, display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.925rem' }}>
                    {dailyIncidents.map((inc) => {
                      const isMacro = inc.impact_scope === 'cumulative_macro_trend' || (inc.financial_damage_usd || 0) >= 5_000_000_000;
                      return (
                        <li
                          key={inc.incident_id}
                          onClick={() => onSelectIncident(inc)}
                          style={{
                            background: 'rgba(255,255,255,0.02)',
                            padding: '0.75rem 0.85rem',
                            borderRadius: '6px',
                            border: '1px solid rgba(255,255,255,0.06)',
                            cursor: 'pointer',
                            transition: 'all 0.15s ease',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.35rem'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'rgba(56, 189, 248, 0.08)';
                            e.currentTarget.style.borderColor = 'rgba(56, 189, 248, 0.3)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'rgba(255,255,255,0.02)';
                            e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)';
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                              <span className={`severity-badge severity-${inc.severity}`} style={{ fontSize: '0.65rem', padding: '0.1rem 0.35rem', textTransform: 'uppercase', fontWeight: 700 }}>
                                {inc.severity}
                              </span>
                              {isMacro ? (
                                <span style={{ fontSize: '0.65rem', background: 'rgba(168, 85, 247, 0.2)', color: '#c084fc', border: '1px solid rgba(168, 85, 247, 0.4)', padding: '0.1rem 0.35rem', borderRadius: '4px', display: 'inline-flex', alignItems: 'center', gap: '0.2rem', fontWeight: 600 }}>
                                  <Globe size={10} /> Macro Trend Report
                                </span>
                              ) : (
                                <span style={{ fontSize: '0.65rem', background: 'rgba(52, 211, 153, 0.15)', color: '#34d399', border: '1px solid rgba(52, 211, 153, 0.3)', padding: '0.1rem 0.35rem', borderRadius: '4px', fontWeight: 600 }}>
                                  📌 Discrete Event
                                </span>
                              )}
                              <strong style={{ color: 'var(--text-main)', fontSize: '0.95rem' }}>{inc.title}</strong>
                            </div>
                            <ExternalLink size={13} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
                          </div>
                          <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                            {inc.summary}{' '}
                            <span style={{ color: (inc.financial_damage_usd || 0) > 0 ? '#34d399' : 'var(--accent-cyan)', fontWeight: 600 }}>
                              (Est. Impact: {formatFinancialDamage(inc.financial_damage_usd)})
                            </span>
                          </p>
                        </li>
                      );
                    })}
                  </ul>
                </div>

                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '0.85rem' }}>
                  * All incident reports are automatically ingested via multi-source harvesting and categorized using CSET & EU AI Act risk taxonomies. Click any incident above to open the full technical drawer.
                </p>
              </div>
            )}
          </article>

        </div>

        {/* RIGHT SIDEBAR: Daily Aggregated Metrics Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', position: 'sticky', top: '5rem' }}>
          
          <div className="detail-section">
            <h4 style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>
              Period Incident Metrics
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

          {/* Discrete Financial Impact Card */}
          <div className="detail-section" style={{ background: 'rgba(52, 211, 153, 0.08)', borderColor: 'rgba(52, 211, 153, 0.25)' }}>
            <h4 style={{ fontSize: '0.75rem', color: '#34d399', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <DollarSign size={14} /> Discrete Single-Event Losses
            </h4>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#34d399', marginBottom: '0.2rem' }}>
              {formatFinancialDamage(discreteTotalUSD)}
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Non-overlapping financial losses from specific single-event hacks, fines, and settlements.
            </p>
          </div>

          {/* Macro Industry Trend Benchmark Card */}
          {macroBenchmarkUSD > 0 && (
            <div className="detail-section" style={{ background: 'rgba(168, 85, 247, 0.08)', borderColor: 'rgba(168, 85, 247, 0.25)' }}>
              <h4 style={{ fontSize: '0.75rem', color: '#c084fc', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Globe size={14} /> Industry Macro Trend Benchmark
              </h4>
              <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#c084fc', marginBottom: '0.2rem' }}>
                {formatFinancialDamage(macroBenchmarkUSD)}
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Aggregated sector threat report totals (e.g. Chainalysis global annual fraud totals). Kept strictly separate to prevent double-counting.
              </p>
            </div>
          )}

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
