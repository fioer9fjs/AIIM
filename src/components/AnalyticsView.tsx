import React from 'react';
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
import { AIIncident } from '../types/incident';

interface AnalyticsViewProps {
  incidents: AIIncident[];
}

const COLORS = ['#ef4444', '#f97316', '#eab308', '#3b82f6', '#10b981', '#8b5cf6'];

export const AnalyticsView: React.FC<AnalyticsViewProps> = ({ incidents }) => {
  // Severity Distribution Data
  const severityCounts = incidents.reduce((acc, inc) => {
    acc[inc.severity] = (acc[inc.severity] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const severityData = Object.entries(severityCounts).map(([name, value]) => ({
    name: name.toUpperCase(),
    value
  }));

  // Harm Domain Data
  const harmCounts = incidents.reduce((acc, inc) => {
    const domain = inc.harm_domain.replace(/_/g, ' ');
    acc[domain] = (acc[domain] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const harmData = Object.entries(harmCounts).map(([name, value]) => ({
    name,
    count: value
  }));

  // System Classification Data
  const systemCounts = incidents.reduce((acc, inc) => {
    const sys = inc.system_classification.replace(/_/g, ' ');
    acc[sys] = (acc[sys] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const systemData = Object.entries(systemCounts).map(([name, value]) => ({
    name,
    count: value
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
        <div className="detail-section">
          <h4>Total Incidents Tracked</h4>
          <p style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>{incidents.length}</p>
        </div>
        <div className="detail-section">
          <h4>Critical Incidents</h4>
          <p style={{ fontSize: '2rem', fontWeight: 700, color: '#ef4444' }}>
            {severityCounts['critical'] || 0}
          </p>
        </div>
        <div className="detail-section">
          <h4>High-Risk Regulated Systems</h4>
          <p style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-purple)' }}>
            {systemCounts['high risk regulated'] || 0}
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.5rem' }}>
        {/* Severity Pie Chart */}
        <div className="detail-section">
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem' }}>Incident Severity Breakdown</h3>
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
                  label={(entry) => entry.name}
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

        {/* Harm Domain Bar Chart */}
        <div className="detail-section">
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem' }}>Harm Domain Distribution (OECD)</h3>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={harmData}>
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
