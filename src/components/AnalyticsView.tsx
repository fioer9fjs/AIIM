import React, { useState, useMemo } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';
import {
  AIIncident,
  formatFinancialDamage,
  computeFinancialImpactTotals
} from '../types/incident';
import {
  RotateCcw,
  Filter,
  DollarSign,
  Globe,
  ShieldAlert,
  Scale,
  Bot,
  AlertTriangle,
  ChevronRight
} from 'lucide-react';

interface AnalyticsViewProps {
  incidents: AIIncident[];
  onSelectIncident: (incident: AIIncident) => void;
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
  undetermined: '#64748b'
};

const EU_TIER_COLORS: Record<string, string> = {
  prohibited: '#dc2626',
  high_risk: '#f97316',
  limited_risk: '#38bdf8',
  minimal_risk: '#10b981',
  unclassified: '#64748b'
};

const INTENT_COLORS: Record<string, string> = {
  intentional_misuse: '#ef4444',
  unintentional_failure: '#3b82f6',
  undetermined: '#64748b'
};

export const AnalyticsView: React.FC<AnalyticsViewProps> = ({ incidents, onSelectIncident }) => {
  const { discreteTotalUSD, macroBenchmarkUSD } = useMemo(() => {
    return computeFinancialImpactTotals(incidents);
  }, [incidents]);

  const [selectedFilter, setSelectedFilter] = useState<{
    type: 'severity' | 'harm' | 'system' | 'eu_tier' | 'intent' | 'root_cause' | 'all';
    value: string;
    label: string;
  }>({
    type: 'all',
    value: 'all',
    label: 'All Incidents'
  });

  // Harm Domain Data (Count & Total USD Loss)
  const harmData = useMemo(() => {
    const counts: Record<string, { count: number; totalUSD: number }> = {};
    incidents.forEach((inc) => {
      const rawDomain = inc.harm_domain || (inc as any).taxonomy?.harm_domain || 'systemic_integrity';
      const clean = rawDomain.replace(/_/g, ' ');
      const label = clean.charAt(0).toUpperCase() + clean.slice(1);
      if (!counts[label]) {
        counts[label] = { count: 0, totalUSD: 0 };
      }
      counts[label].count += 1;
      counts[label].totalUSD += inc.financial_damage_usd || 0;
    });
    return Object.entries(counts)
      .map(([name, data]) => ({
        name,
        count: data.count,
        totalUSD: data.totalUSD,
        totalUSDM: Number((data.totalUSD / 1_000_000).toFixed(1))
      }))
      .sort((a, b) => b.count - a.count);
  }, [incidents]);

  // System Classification Data
  const systemData = useMemo(() => {
    const counts: Record<string, number> = {};
    incidents.forEach((inc) => {
      const rawSys = inc.system_classification || (inc as any).taxonomy?.system_classification || 'general_purpose_model';
      const clean = rawSys.replace(/_/g, ' ');
      const label = clean.charAt(0).toUpperCase() + clean.slice(1);
      counts[label] = (counts[label] || 0) + 1;
    });
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count);
  }, [incidents]);

  // EU AI Act Risk Tier Distribution
  const euTierData = useMemo(() => {
    const counts: Record<string, number> = {};
    incidents.forEach((inc) => {
      const rawTier = inc.eu_ai_act_tier || (inc as any).taxonomy?.eu_ai_act_tier || 'high_risk';
      counts[rawTier] = (counts[rawTier] || 0) + 1;
    });
    return Object.entries(counts).map(([rawTier, value]) => {
      const clean = rawTier.replace(/_/g, ' ');
      const label = clean.charAt(0).toUpperCase() + clean.slice(1);
      return {
        name: label,
        rawTier,
        value,
        color: EU_TIER_COLORS[rawTier] || '#64748b'
      };
    });
  }, [incidents]);

  // Intent (Unintentional Failure vs Intentional Misuse)
  const intentData = useMemo(() => {
    const counts: Record<string, number> = {};
    incidents.forEach((inc) => {
      const rawIntent = inc.intent || (inc as any).taxonomy?.intent || 'unintentional_failure';
      counts[rawIntent] = (counts[rawIntent] || 0) + 1;
    });
    return Object.entries(counts).map(([rawIntent, value]) => {
      const clean = rawIntent.replace(/_/g, ' ');
      const label = clean.charAt(0).toUpperCase() + clean.slice(1);
      return {
        name: label,
        rawIntent,
        value,
        color: INTENT_COLORS[rawIntent] || '#64748b'
      };
    });
  }, [incidents]);

  // Root Cause Category Data
  const rootCauseData = useMemo(() => {
    const counts: Record<string, number> = {};
    incidents.forEach((inc) => {
      const rawRc = inc.root_cause_category || (inc as any).taxonomy?.root_cause_category || 'governance';
      const clean = rawRc.replace(/_/g, ' ');
      const label = clean.charAt(0).toUpperCase() + clean.slice(1);
      counts[label] = (counts[label] || 0) + 1;
    });
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count);
  }, [incidents]);

  // High-Risk EU AI Act Count
  const highRiskCount = useMemo(() => {
    return incidents.filter((i) => {
      const tier = i.eu_ai_act_tier || (i as any).taxonomy?.eu_ai_act_tier;
      return tier === 'high_risk' || tier === 'prohibited';
    }).length;
  }, [incidents]);

  // Critical Count
  const criticalCount = useMemo(() => {
    return incidents.filter((i) => i.severity === 'critical').length;
  }, [incidents]);

  // Filtered Incidents for Drill-Down Table
  const drillDownIncidents = useMemo(() => {
    if (selectedFilter.type === 'all') return incidents;

    return incidents.filter((inc) => {
      if (selectedFilter.type === 'severity') {
        return (inc.severity || 'medium').toLowerCase() === selectedFilter.value.toLowerCase();
      }
      if (selectedFilter.type === 'harm') {
        const dom = (inc.harm_domain || (inc as any).taxonomy?.harm_domain || '').replace(/_/g, ' ').toLowerCase();
        return dom === selectedFilter.value.toLowerCase();
      }
      if (selectedFilter.type === 'system') {
        const sys = (inc.system_classification || (inc as any).taxonomy?.system_classification || '').replace(/_/g, ' ').toLowerCase();
        return sys === selectedFilter.value.toLowerCase();
      }
      if (selectedFilter.type === 'eu_tier') {
        const tier = inc.eu_ai_act_tier || (inc as any).taxonomy?.eu_ai_act_tier || '';
        return tier.toLowerCase() === selectedFilter.value.toLowerCase();
      }
      if (selectedFilter.type === 'intent') {
        const intent = inc.intent || (inc as any).taxonomy?.intent || '';
        return intent.toLowerCase() === selectedFilter.value.toLowerCase();
      }
      if (selectedFilter.type === 'root_cause') {
        const rc = (inc.root_cause_category || (inc as any).taxonomy?.root_cause_category || '').replace(/_/g, ' ').toLowerCase();
        return rc === selectedFilter.value.toLowerCase();
      }
      return true;
    });
  }, [incidents, selectedFilter]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* 1. Executive Telemetry KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '1rem' }}>
        <div className="detail-section">
          <h4>Total Incidents Tracked</h4>
          <p style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>{incidents.length}</p>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Real-world operational catalog</span>
        </div>

        <div className="detail-section" style={{ borderColor: 'rgba(52, 211, 153, 0.3)' }}>
          <h4 style={{ color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <DollarSign size={14} /> Discrete Single Losses
          </h4>
          <p style={{ fontSize: '1.8rem', fontWeight: 700, color: '#34d399' }}>
            {formatFinancialDamage(discreteTotalUSD)}
          </p>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Confirmed & reported incident sum</span>
        </div>

        <div className="detail-section" style={{ borderColor: 'rgba(168, 85, 247, 0.3)' }}>
          <h4 style={{ color: '#c084fc', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <Globe size={14} /> Macro Industry Benchmark
          </h4>
          <p style={{ fontSize: '1.8rem', fontWeight: 700, color: '#c084fc' }}>
            {formatFinancialDamage(macroBenchmarkUSD)}
          </p>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Aggregated market & annual totals</span>
        </div>

        <div className="detail-section" style={{ borderColor: 'rgba(239, 68, 68, 0.3)' }}>
          <h4 style={{ color: '#ef4444', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <AlertTriangle size={14} /> Critical Severity
          </h4>
          <p style={{ fontSize: '1.8rem', fontWeight: 700, color: '#ef4444' }}>
            {criticalCount}
          </p>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Fatalities, systemic breach, class actions</span>
        </div>

        <div className="detail-section" style={{ borderColor: 'rgba(249, 115, 22, 0.3)' }}>
          <h4 style={{ color: '#f97316', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <Scale size={14} /> High-Risk & Prohibited
          </h4>
          <p style={{ fontSize: '1.8rem', fontWeight: 700, color: '#f97316' }}>
            {highRiskCount}
          </p>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>EU AI Act Annex III Scope ({((highRiskCount / incidents.length) * 100).toFixed(0)}%)</span>
        </div>
      </div>

      {/* 2. Primary Threat Exposure Grid (Harm Domains & Financial Damage) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '1.5rem' }}>
        {/* Harm Domain Distribution Horizontal Bar Chart */}
        <div className="detail-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Harm Domain Distribution</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Categorization by impacted societal asset (Click bar to filter)</p>
            </div>
            <ShieldAlert size={18} style={{ color: 'var(--accent-purple)' }} />
          </div>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={harmData}
                margin={{ top: 5, right: 30, left: 120, bottom: 5 }}
              >
                <XAxis type="number" stroke="#94a3b8" fontSize={11} />
                <YAxis
                  type="category"
                  dataKey="name"
                  stroke="#94a3b8"
                  fontSize={11}
                  interval={0}
                  tick={{ fill: '#e2e8f0' }}
                  width={115}
                />
                <Tooltip
                  formatter={(val: any) => [`${val} Incidents`, 'Count']}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '6px' }}
                />
                <Bar
                  dataKey="count"
                  fill="#8b5cf6"
                  radius={[0, 4, 4, 0]}
                  style={{ cursor: 'pointer' }}
                  onClick={(entry) => {
                    if (entry && entry.name) {
                      setSelectedFilter({
                        type: 'harm',
                        value: entry.name,
                        label: `Harm Domain: ${entry.name}`
                      });
                    }
                  }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Financial Damage Exposure by Harm Domain Bar Chart */}
        <div className="detail-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Financial Damage by Harm Domain</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Aggregated empirical & confirmed USD damages ($M)</p>
            </div>
            <DollarSign size={18} style={{ color: '#34d399' }} />
          </div>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={harmData}
                margin={{ top: 5, right: 30, left: 120, bottom: 5 }}
              >
                <XAxis type="number" stroke="#94a3b8" fontSize={11} unit="M" />
                <YAxis
                  type="category"
                  dataKey="name"
                  stroke="#94a3b8"
                  fontSize={11}
                  interval={0}
                  tick={{ fill: '#e2e8f0' }}
                  width={115}
                />
                <Tooltip
                  formatter={(val: any) => [`$${val}M USD`, 'Damage']}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '6px' }}
                />
                <Bar
                  dataKey="totalUSDM"
                  fill="#34d399"
                  radius={[0, 4, 4, 0]}
                  style={{ cursor: 'pointer' }}
                  onClick={(entry) => {
                    if (entry && entry.name) {
                      setSelectedFilter({
                        type: 'harm',
                        value: entry.name,
                        label: `Harm Domain: ${entry.name}`
                      });
                    }
                  }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* 3. System Architecture & Regulatory Scope Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '1.5rem' }}>
        {/* System Classification Horizontal Bar Chart */}
        <div className="detail-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>System Classification</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Architectural deployment type (Frontier LLM, Autonomous Agent, Vision)</p>
            </div>
            <Bot size={18} style={{ color: 'var(--accent-cyan)' }} />
          </div>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={systemData}
                margin={{ top: 5, right: 30, left: 130, bottom: 5 }}
              >
                <XAxis type="number" stroke="#94a3b8" fontSize={11} />
                <YAxis
                  type="category"
                  dataKey="name"
                  stroke="#94a3b8"
                  fontSize={11}
                  interval={0}
                  tick={{ fill: '#e2e8f0' }}
                  width={125}
                />
                <Tooltip
                  formatter={(val: any) => [`${val} Incidents`, 'Count']}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '6px' }}
                />
                <Bar
                  dataKey="count"
                  fill="#38bdf8"
                  radius={[0, 4, 4, 0]}
                  style={{ cursor: 'pointer' }}
                  onClick={(entry) => {
                    if (entry && entry.name) {
                      setSelectedFilter({
                        type: 'system',
                        value: entry.name,
                        label: `System: ${entry.name}`
                      });
                    }
                  }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* EU AI Act Risk Tier Donut Chart */}
        <div className="detail-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>EU AI Act Risk Classification</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Statutory compliance tier distribution (Click slice to filter)</p>
            </div>
            <Scale size={18} style={{ color: '#f97316' }} />
          </div>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={euTierData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                  style={{ cursor: 'pointer' }}
                  onClick={(entry) => {
                    if (entry && entry.rawTier) {
                      setSelectedFilter({
                        type: 'eu_tier',
                        value: entry.rawTier,
                        label: `EU AI Act: ${entry.name}`
                      });
                    }
                  }}
                >
                  {euTierData.map((entry, index) => (
                    <Cell key={`tier-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val: any) => [`${val} Incidents`, 'Volume']}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '6px' }}
                />
                <Legend verticalAlign="bottom" height={36} iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* 4. Intent & Root Cause Causality Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '1.5rem' }}>
        {/* Intent Distribution: Failure vs Adversarial Misuse */}
        <div className="detail-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Adversarial Misuse vs. Unintentional Failure</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Malicious exploit vs. internal model/governance breakdown</p>
            </div>
            <AlertTriangle size={18} style={{ color: '#ef4444' }} />
          </div>
          <div style={{ width: '100%', height: 240 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={intentData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={4}
                  label={({ name, value }) => `${name}: ${value}`}
                  style={{ cursor: 'pointer' }}
                  onClick={(entry) => {
                    if (entry && entry.rawIntent) {
                      setSelectedFilter({
                        type: 'intent',
                        value: entry.rawIntent,
                        label: `Intent: ${entry.name}`
                      });
                    }
                  }}
                >
                  {intentData.map((entry, index) => (
                    <Cell key={`intent-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '6px' }} />
                <Legend verticalAlign="bottom" height={36} iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Root Cause Category Horizontal Bar Chart */}
        <div className="detail-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Root Cause Drivers</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Originating fault mechanism (Model, Human, Governance, External)</p>
            </div>
            <Scale size={18} style={{ color: '#38bdf8' }} />
          </div>
          <div style={{ width: '100%', height: 240 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={rootCauseData}
                margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
              >
                <XAxis type="number" stroke="#94a3b8" fontSize={11} />
                <YAxis
                  type="category"
                  dataKey="name"
                  stroke="#94a3b8"
                  fontSize={11}
                  interval={0}
                  tick={{ fill: '#e2e8f0' }}
                  width={95}
                />
                <Tooltip
                  formatter={(val: any) => [`${val} Incidents`, 'Count']}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '6px' }}
                />
                <Bar
                  dataKey="count"
                  fill="#f59e0b"
                  radius={[0, 4, 4, 0]}
                  style={{ cursor: 'pointer' }}
                  onClick={(entry) => {
                    if (entry && entry.name) {
                      setSelectedFilter({
                        type: 'root_cause',
                        value: entry.name,
                        label: `Root Cause: ${entry.name}`
                      });
                    }
                  }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* 5. Interactive Drill-Down Filtered Incidents Explorer */}
      <div className="detail-section" style={{ marginTop: '1rem', borderTop: '2px solid var(--border-light)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Filter size={18} style={{ color: 'var(--accent-cyan)' }} />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>
              Filtered Incident List: <span style={{ color: 'var(--accent-purple)' }}>{selectedFilter.label}</span>
            </h3>
            <span className="badge" style={{ backgroundColor: 'rgba(56, 189, 248, 0.2)', color: 'var(--accent-cyan)' }}>
              {drillDownIncidents.length} matching
            </span>
          </div>

          {selectedFilter.type !== 'all' && (
            <button
              onClick={() => setSelectedFilter({ type: 'all', value: 'all', label: 'All Incidents' })}
              className="button button-outline"
              style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}
            >
              <RotateCcw size={13} /> Reset Filter
            </button>
          )}
        </div>

        {drillDownIncidents.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No incidents match the selected chart segment.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {drillDownIncidents.slice(0, 50).map((inc) => {
              const cleanHarm = (inc.harm_domain || (inc as any).taxonomy?.harm_domain || '').replace(/_/g, ' ');
              const cleanSys = (inc.system_classification || (inc as any).taxonomy?.system_classification || '').replace(/_/g, ' ');
              const tier = (inc.eu_ai_act_tier || (inc as any).taxonomy?.eu_ai_act_tier || '').replace(/_/g, ' ');

              return (
                <div
                  key={inc.incident_id}
                  onClick={() => onSelectIncident(inc)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.85rem 1rem',
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border-light)',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    gap: '1rem',
                    transition: 'all 0.15s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'var(--accent-cyan)';
                    e.currentTarget.style.background = 'rgba(56, 189, 248, 0.05)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'var(--border-light)';
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)';
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                        {inc.incident_id}
                      </span>
                      <span
                        className="badge"
                        style={{
                          backgroundColor: `${SEVERITY_COLORS[inc.severity] || '#64748b'}20`,
                          color: SEVERITY_COLORS[inc.severity] || '#64748b'
                        }}
                      >
                        {inc.severity.toUpperCase()}
                      </span>
                      {cleanHarm && (
                        <span className="badge" style={{ backgroundColor: 'rgba(139, 92, 246, 0.15)', color: '#c084fc' }}>
                          {cleanHarm}
                        </span>
                      )}
                      {cleanSys && (
                        <span className="badge" style={{ backgroundColor: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8' }}>
                          {cleanSys}
                        </span>
                      )}
                      {tier && (
                        <span className="badge" style={{ backgroundColor: 'rgba(249, 115, 22, 0.15)', color: '#fb923c' }}>
                          {tier}
                        </span>
                      )}
                    </div>
                    <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#f8fafc', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {inc.title}
                    </span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {inc.date} • {inc.financial_damage_usd && inc.financial_damage_usd > 0 ? formatFinancialDamage(inc.financial_damage_usd) : 'Empirical Benchmark'}
                    </span>
                  </div>

                  <ChevronRight size={18} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
                </div>
              );
            })}
            {drillDownIncidents.length > 50 && (
              <p style={{ textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                Showing first 50 of {drillDownIncidents.length} matching incidents.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
