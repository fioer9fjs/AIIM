import React, { useState, useMemo } from 'react';
import { Search, ArrowUpDown, GitCommit, ShieldAlert, Zap } from 'lucide-react';
import { AIIncident } from '../types/incident';

interface ExplorerViewProps {
  incidents: AIIncident[];
  onSelectIncident: (incident: AIIncident) => void;
}

const SEVERITY_RANK: Record<string, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1
};

export const ExplorerView: React.FC<ExplorerViewProps> = ({ incidents, onSelectIncident }) => {
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [systemFilter, setSystemFilter] = useState<string>('all');
  const [intentFilter, setIntentFilter] = useState<string>('all');
  const [euFilter, setEuFilter] = useState<string>('all');
  const [purposeFilter, setPurposeFilter] = useState<string>('all');
  const [natsecFilter, setNatsecFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('date-desc');

  const filteredAndSortedIncidents = useMemo(() => {
    const list = incidents.filter((inc) => {
      const matchesSearch =
        search === '' ||
        inc.title.toLowerCase().includes(search.toLowerCase()) ||
        inc.summary.toLowerCase().includes(search.toLowerCase()) ||
        (inc.affected_parties && inc.affected_parties.some((p) => p.toLowerCase().includes(search.toLowerCase())));

      const matchesSeverity = severityFilter === 'all' || inc.severity === severityFilter;
      const matchesStatus = statusFilter === 'all' || inc.verification_status === statusFilter;
      const matchesSystem = systemFilter === 'all' || inc.system_classification === systemFilter;
      const matchesIntent = intentFilter === 'all' || inc.intent === intentFilter;
      const matchesEu = euFilter === 'all' || inc.eu_ai_act_tier === euFilter;
      const matchesPurpose = purposeFilter === 'all' || inc.primary_purpose === purposeFilter;
      const matchesNatsec = natsecFilter === 'all' || (natsecFilter === 'yes' ? inc.natsec_impact === true : inc.natsec_impact === false);

      return matchesSearch && matchesSeverity && matchesStatus && matchesSystem && matchesIntent && matchesEu && matchesPurpose && matchesNatsec;
    });

    return list.sort((a, b) => {
      if (sortBy === 'date-desc') {
        return (b.date || '').localeCompare(a.date || '');
      } else if (sortBy === 'date-asc') {
        return (a.date || '').localeCompare(b.date || '');
      } else if (sortBy === 'entity-asc') {
        const entityA = (a.affected_parties?.[0] || a.title).toLowerCase();
        const entityB = (b.affected_parties?.[0] || b.title).toLowerCase();
        return entityA.localeCompare(entityB);
      } else if (sortBy === 'entity-desc') {
        const entityA = (a.affected_parties?.[0] || a.title).toLowerCase();
        const entityB = (b.affected_parties?.[0] || b.title).toLowerCase();
        return entityB.localeCompare(entityA);
      } else if (sortBy === 'severity-desc') {
        return (SEVERITY_RANK[b.severity] || 0) - (SEVERITY_RANK[a.severity] || 0);
      } else if (sortBy === 'severity-asc') {
        return (SEVERITY_RANK[a.severity] || 0) - (SEVERITY_RANK[b.severity] || 0);
      } else if (sortBy === 'confidence-desc') {
        return (b.confidence_scores?.severity || 1.0) - (a.confidence_scores?.severity || 1.0);
      }
      return 0;
    });
  }, [incidents, search, severityFilter, statusFilter, systemFilter, intentFilter, euFilter, purposeFilter, natsecFilter, sortBy]);

  return (
    <div>
      {/* Controls / Filters & Sort */}
      <div className="controls-bar" style={{ borderRadius: '8px', marginBottom: '1.5rem', gap: '0.6rem', flexWrap: 'wrap' }}>
        <div className="search-input-wrapper" style={{ minWidth: '240px' }}>
          <Search className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Search global AI incidents by entity, title, keywords..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {/* Sort Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <ArrowUpDown size={14} style={{ color: 'var(--accent-cyan)' }} />
          <select
            className="filter-select"
            style={{ borderColor: 'var(--accent-cyan)' }}
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="date-desc">Sort: Date (Newest First)</option>
            <option value="date-asc">Sort: Date (Oldest First)</option>
            <option value="entity-asc">Sort: Affected Entity (A-Z)</option>
            <option value="entity-desc">Sort: Affected Entity (Z-A)</option>
            <option value="severity-desc">Sort: Severity (Highest First)</option>
            <option value="severity-asc">Sort: Severity (Lowest First)</option>
            <option value="confidence-desc">Sort: Confidence (Highest First)</option>
          </select>
        </div>

        {/* MIT & AIID Filters */}
        <select
          className="filter-select"
          value={intentFilter}
          onChange={(e) => setIntentFilter(e.target.value)}
          title="Filter by Intent (MIT AI Risk Repository)"
        >
          <option value="all">All Intent Types</option>
          <option value="intentional_misuse">Intentional Misuse</option>
          <option value="unintentional_failure">Unintentional System Failure</option>
        </select>

        <select
          className="filter-select"
          value={euFilter}
          onChange={(e) => setEuFilter(e.target.value)}
          title="Filter by EU AI Act Risk Tier"
        >
          <option value="all">All EU AI Act Tiers</option>
          <option value="prohibited">Prohibited / Unacceptable Risk</option>
          <option value="high_risk">High Risk (Annex III)</option>
          <option value="limited_risk">Limited Risk (Transparency)</option>
          <option value="minimal_risk">Minimal Risk</option>
        </select>

        <select
          className="filter-select"
          value={purposeFilter}
          onChange={(e) => setPurposeFilter(e.target.value)}
          title="Filter by Primary AI Purpose"
        >
          <option value="all">All AI Purpose Sectors</option>
          <option value="generative_content">Generative Content</option>
          <option value="autonomous_mobility">Autonomous Mobility</option>
          <option value="biometric_surveillance">Biometric Surveillance</option>
          <option value="financial_fintech">Financial / Fintech</option>
          <option value="healthcare_medical">Healthcare & Medical</option>
          <option value="recruitment_hr">Recruitment & HR</option>
          <option value="defense_national_security">Defense & NatSec</option>
        </select>

        <select
          className="filter-select"
          value={natsecFilter}
          onChange={(e) => setNatsecFilter(e.target.value)}
          title="Filter by National Security Impact"
        >
          <option value="all">All NatSec Statuses</option>
          <option value="yes">NatSec Impact: Yes</option>
          <option value="no">NatSec Impact: No</option>
        </select>

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
          <option value="all">All Statuses</option>
          <option value="confirmed">Confirmed</option>
          <option value="alleged">Alleged</option>
          <option value="disputed">Disputed</option>
        </select>
      </div>

      {/* Grid of Incidents */}
      <div className="grid-cards">
        {filteredAndSortedIncidents.map((inc) => (
          <div key={inc.incident_id} className="incident-card" onClick={() => onSelectIncident(inc)}>
            <div className="card-header">
              <span className={`badge badge-${inc.severity}`}>{inc.severity}</span>
              <span className={`badge badge-${inc.verification_status}`}>{inc.verification_status}</span>
              {inc.eu_ai_act_tier && (
                <span className="badge" style={{ backgroundColor: 'rgba(59, 130, 246, 0.2)', color: '#93c5fd' }}>
                  EU: {inc.eu_ai_act_tier.replace('_', ' ')}
                </span>
              )}
              {inc.natsec_impact && (
                <span className="badge" style={{ backgroundColor: 'rgba(239, 68, 68, 0.25)', color: '#fca5a5', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                  <ShieldAlert size={12} /> NatSec
                </span>
              )}
            </div>

            <h3 className="card-title">{inc.title}</h3>
            <p className="card-summary">{inc.summary}</p>

            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {inc.intent && (
                <span className="confidence-tag" style={{ color: inc.intent === 'intentional_misuse' ? '#f87171' : '#a7f3d0' }}>
                  <Zap size={11} style={{ marginRight: '3px' }} />
                  {inc.intent.replace('_', ' ')}
                </span>
              )}
              <span className="confidence-tag" style={{ color: 'var(--accent-cyan)' }}>
                {inc.affected_parties?.[0] ? `Entity: ${inc.affected_parties[0]}` : inc.system_classification.replace(/_/g, ' ')}
              </span>
              <span className="confidence-tag" style={{ color: 'var(--accent-purple)' }}>
                {inc.harm_domain.replace(/_/g, ' ')}
              </span>
            </div>

            <div className="card-footer">
              <span>{inc.date}</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {inc.related_incidents && inc.related_incidents.length > 0 && (
                  <span style={{ color: 'var(--accent-blue)', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                    <GitCommit size={14} /> {inc.related_incidents.length} Edge(s)
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredAndSortedIncidents.length === 0 && (
        <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
          No AI incidents match the selected search & filter criteria.
        </div>
      )}
    </div>
  );
};
