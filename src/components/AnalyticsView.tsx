import React, { useState, useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { AIIncident, formatFinancialDamage, computeFinancialImpactTotals } from '../types/incident';

import { RotateCcw, Filter, DollarSign, Globe, ShieldAlert } from 'lucide-react';

interface AnalyticsViewProps {
  incidents: AIIncident[];
  onSelectIncident: (incident: AIIncident) => void;
}

const COLORS = ['#ef4444', '#f97316', '#eab308', '#3b82f6', '#10b981', '#8b5cf6'];

export const AnalyticsView: React.FC<AnalyticsViewProps> = ({ incidents, onSelectIncident }) => {
  const { discreteTotalUSD, macroBenchmarkUSD } = useMemo(() => {
    return computeFinancialImpactTotals(incidents);
  }, [incidents]);

  const [selectedFilter, setSelectedFilter] = useState<{ type: 'severity' | 'harm' | 'system' | 'all'; value: string; label: string }>({
    type: 'all',
    value: 'all',
    label: 'All Incidents'
  });

  // Severity Distribution Data
  const severityCounts = useMemo(() => {
    return incidents.reduce((acc, inc) => {
      acc[inc.severity] = (acc[inc.severity] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [incidents]);

  const severityData = useMemo(() => {
    return Object.entries(severityCounts).map(([name, value]) => ({
      name: name.toUpperCase(),
      rawName: name,
      value
    }));
  }, [severityCounts]);

  // Harm Domain Data
  const harmCounts = useMemo(() => {
    return incidents.reduce((acc, inc) => {
      const domain = inc.harm_domain.replace(/_/g, ' ');
      acc[domain] = (acc[domain] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [incidents]);

  const harmData = useMemo(() => {
    return Object.entries(harmCounts).map(([name, value]) => ({
      name,
      count: value
    }));
  }, [harmCounts]);

  // System Classification Data
  const systemCounts = useMemo(() => {
    return incidents.reduce((acc, inc) => {
      const sys = inc.system_classification.replace(/_/g, ' ');
      acc[sys] = (acc[sys] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [incidents]);

  const systemData = useMemo(() => {
    return Object.entries(systemCounts).map(([name, value]) => ({
      name,
      count: value
    }));
  }, [systemCounts]);

  // Drill-Down Filtered List
  const drillDownIncidents = useMemo(() => {
    if (selectedFilter.type === 'all') return incidents;
    
    return incidents.filter((inc) => {
      if (selectedFilter.type === 'severity') {
        return inc.severity.toLowerCase() === selectedFilter.value.toLowerCase();
      }
      if (selectedFilter.type === 'harm') {
        return inc.harm_domain.replace(/_/g, ' ').toLowerCase() === selectedFilter.value.toLowerCase();
      }
      if (selectedFilter.type === 'system') {
        return inc.system_classification.replace(/_/g, ' ').toLowerCase() === selectedFilter.value.toLowerCase();
      }
      return true;
    });
  }, [incidents, selectedFilter]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Overview Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div className="detail-section">
          <h4>Total Incidents Tracked</h4>
          <p style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>{incidents.length}</p>
        </div>
        <div className="detail-section" style={{ borderColor: 'rgba(52, 211, 153, 0.3)' }}>
          <h4 style={{ color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <DollarSign size={14} /> Discrete Single Losses
          </h4>
          <p style={{ fontSize: '1.8rem', fontWeight: 700, color: '#34d399' }}>
            {formatFinancialDamage(discreteTotalUSD)}
          </p>
        </div>
        <div className="detail-section" style={{ borderColor: 'rgba(168, 85, 247, 0.3)' }}>
          <h4 style={{ color: '#c084fc', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <Globe size={14} /> Macro Industry Benchmark
          </h4>
          <p style={{ fontSize: '1.8rem', fontWeight: 700, color: '#c084fc' }}>
            {formatFinancialDamage(macroBenchmarkUSD)}
          </p>
        </div>
        <div className="detail-section">
          <h4>Critical Incidents</h4>
          <p style={{ fontSize: '1.8rem', fontWeight: 700, color: '#ef4444' }}>
            {severityCounts['critical'] || 0}
          </p>
        </div>
      </div>

      {/* Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
        {/* Severity Pie Chart */}
        <div className="detail-section" style={{ position: 'relative' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>
            Incident Severity Breakdown <span style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>(Click segment to filter)</span>
          </h3>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severityData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={(entry) => `${entry.name} (${entry.value})`}
                  style={{ cursor: 'pointer' }}
                  onClick={(entry) => {
                    if (entry && entry.rawName) {
                      setSelectedFilter({
                        type: 'severity',
                        value: entry.rawName,
                        label: `Severity: ${entry.name}`
                      });
                    }
                  }}
                >
                  {severityData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Harm Domain Distribution Bar Chart */}
        <div className="detail-section">
          <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>
            Harm Domain Distribution <span style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>(Click bar to filter)</span>
          </h3>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={harmData}>
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} interval={0} angle={-15} textAnchor="end" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Bar
                  dataKey="count"
                  fill="var(--accent-purple)"
                  radius={[4, 4, 0, 0]}
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

        {/* System Classification Bar Chart */}
        <div className="detail-section" style={{ gridColumn: '1 / -1' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>
            System Classification <span style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>(Click bar to filter)</span>
          </h3>
          <div style={{ width: '100%', height: 240 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={systemData}>
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Bar
                  dataKey="count"
                  fill="var(--accent-cyan)"
                  radius={[4, 4, 0, 0]}
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
      </div>

      {/* Interactive Drill-Down Filtered Incidents List */}
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
              <RotateCcw size={13} /> Reset Chart Filter
            </button>
          )}
        </div>

        {drillDownIncidents.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No incidents match the selected chart segment.</p>
        ) : (
          <div className="grid-cards">
            {drillDownIncidents.map((inc) => (
              <div key={inc.incident_id} className="incident-card" onClick={() => onSelectIncident(inc)}>
                <div className="card-header">
                  <span className={`badge badge-${inc.severity}`}>{inc.severity}</span>
                  <span className={`badge badge-${inc.verification_status}`}>{inc.verification_status}</span>
                  <span className="badge" style={{ backgroundColor: 'rgba(168, 85, 247, 0.2)', color: '#d8b4fe' }}>
                    Src: {(inc.source_type || 'google_news_rss').replace(/_/g, ' ')}
                  </span>
                  {inc.financial_damage_usd ? inc.financial_damage_usd > 0 ? (
                    <span className="badge" style={{ backgroundColor: 'rgba(16, 185, 129, 0.2)', color: '#34d399', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
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
                  <span className="details-link">Details →</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
