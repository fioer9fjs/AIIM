import React, { useState, useMemo } from 'react';
import { Search, Filter, ExternalLink, GitCommit } from 'lucide-react';
import { AIIncident, Severity, VerificationStatus, SystemClassification } from '../types/incident';

interface ExplorerViewProps {
  incidents: AIIncident[];
  onSelectIncident: (incident: AIIncident) => void;
}

export const ExplorerView: React.FC<ExplorerViewProps> = ({ incidents, onSelectIncident }) => {
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [systemFilter, setSystemFilter] = useState<string>('all');

  const filteredIncidents = useMemo(() => {
    return incidents.filter((inc) => {
      const matchesSearch =
        search === '' ||
        inc.title.toLowerCase().includes(search.toLowerCase()) ||
        inc.summary.toLowerCase().includes(search.toLowerCase()) ||
        inc.affected_parties.some((p) => p.toLowerCase().includes(search.toLowerCase()));

      const matchesSeverity = severityFilter === 'all' || inc.severity === severityFilter;
      const matchesStatus = statusFilter === 'all' || inc.verification_status === statusFilter;
      const matchesSystem = systemFilter === 'all' || inc.system_classification === systemFilter;

      return matchesSearch && matchesSeverity && matchesStatus && matchesSystem;
    });
  }, [incidents, search, severityFilter, statusFilter, systemFilter]);

  return (
    <div>
      {/* Controls / Filters */}
      <div className="controls-bar" style={{ borderRadius: '8px', marginBottom: '1.5rem' }}>
        <div className="search-input-wrapper">
          <Search className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Search global AI incidents by entity, title, keywords..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <select
          className="filter-select"
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
        >
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        <select
          className="filter-select"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="all">All Verification Statuses</option>
          <option value="confirmed">Confirmed</option>
          <option value="alleged">Alleged</option>
          <option value="disputed">Disputed</option>
        </select>

        <select
          className="filter-select"
          value={systemFilter}
          onChange={(e) => setSystemFilter(e.target.value)}
        >
          <option value="all">All System Types</option>
          <option value="autonomous_agent">Autonomous Agent</option>
          <option value="general_purpose_model">General-Purpose Model</option>
          <option value="high_risk_regulated">High-Risk Regulated</option>
          <option value="dual_use_security">Dual-Use / Security</option>
        </select>
      </div>

      {/* Grid of Incidents */}
      <div className="grid-cards">
        {filteredIncidents.map((inc) => (
          <div key={inc.incident_id} className="incident-card" onClick={() => onSelectIncident(inc)}>
            <div className="card-header">
              <span className={`badge badge-${inc.severity}`}>{inc.severity}</span>
              <span className={`badge badge-${inc.verification_status}`}>{inc.verification_status}</span>
              <span className="confidence-tag" title="Extraction confidence">
                {(inc.confidence_scores?.severity ?? 1.0) * 100}% Conf.
              </span>
            </div>

            <h3 className="card-title">{inc.title}</h3>
            <p className="card-summary">{inc.summary}</p>

            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <span className="confidence-tag" style={{ color: 'var(--accent-cyan)' }}>
                {inc.system_classification.replace(/_/g, ' ')}
              </span>
              <span className="confidence-tag" style={{ color: 'var(--accent-purple)' }}>
                {inc.harm_domain.replace(/_/g, ' ')}
              </span>
            </div>

            <div className="card-footer">
              <span>{inc.date}</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {inc.related_incidents.length > 0 && (
                  <span style={{ color: 'var(--accent-blue)', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                    <GitCommit size={14} /> {inc.related_incidents.length} Graph Edge(s)
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredIncidents.length === 0 && (
        <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
          No AI incidents match the selected search & filter criteria.
        </div>
      )}
    </div>
  );
};
