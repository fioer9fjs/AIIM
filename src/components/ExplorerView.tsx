import React, { useState, useMemo } from 'react';
import { Search, ArrowUpDown, ShieldAlert, Filter, RotateCcw, DollarSign, Globe, ChevronDown, ChevronUp, X, ChevronRight } from 'lucide-react';
import { AIIncident, formatFinancialDamage } from '../types/incident';

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
  const [sourceFilter, setSourceFilter] = useState<string>('all');
  const [countryFilter, setCountryFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('date-desc');

  // Toggle for Advanced Taxonomy Accordion in Left Sidebar
  const [showAdvancedFilters, setShowAdvancedFilters] = useState<boolean>(false);

  const uniqueCountries = useMemo(() => {
    const set = new Set<string>();
    incidents.forEach((inc) => {
      if (inc.geographic_scope) {
        inc.geographic_scope.forEach((c) => set.add(c));
      }
    });
    return Array.from(set).sort();
  }, [incidents]);

  const handleResetFilters = () => {
    setSearch('');
    setSeverityFilter('all');
    setStatusFilter('all');
    setSystemFilter('all');
    setIntentFilter('all');
    setEuFilter('all');
    setPurposeFilter('all');
    setNatsecFilter('all');
    setSourceFilter('all');
    setCountryFilter('all');
    setSortBy('date-desc');
  };

  // Active filter chips calculation
  const activeChips = useMemo(() => {
    const chips: { label: string; reset: () => void }[] = [];
    if (search) chips.push({ label: `Search: "${search}"`, reset: () => setSearch('') });
    if (severityFilter !== 'all') chips.push({ label: `Severity: ${severityFilter}`, reset: () => setSeverityFilter('all') });
    if (sourceFilter !== 'all') chips.push({ label: `Source: ${sourceFilter.replace(/_/g, ' ')}`, reset: () => setSourceFilter('all') });
    if (countryFilter !== 'all') chips.push({ label: `Country: ${countryFilter}`, reset: () => setCountryFilter('all') });
    if (euFilter !== 'all') chips.push({ label: `EU AI Act: ${euFilter.replace(/_/g, ' ')}`, reset: () => setEuFilter('all') });
    if (intentFilter !== 'all') chips.push({ label: `Intent: ${intentFilter.replace(/_/g, ' ')}`, reset: () => setIntentFilter('all') });
    if (purposeFilter !== 'all') chips.push({ label: `Purpose: ${purposeFilter.replace(/_/g, ' ')}`, reset: () => setPurposeFilter('all') });
    if (natsecFilter !== 'all') chips.push({ label: `NatSec: ${natsecFilter}`, reset: () => setNatsecFilter('all') });
    if (statusFilter !== 'all') chips.push({ label: `Status: ${statusFilter}`, reset: () => setStatusFilter('all') });
    return chips;
  }, [search, severityFilter, sourceFilter, countryFilter, euFilter, intentFilter, purposeFilter, natsecFilter, statusFilter]);

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
      const matchesSource = sourceFilter === 'all' || (inc.source_type || 'google_news_rss') === sourceFilter;
      const matchesCountry = countryFilter === 'all' || (inc.geographic_scope && inc.geographic_scope.includes(countryFilter));

      return (
        matchesSearch &&
        matchesSeverity &&
        matchesStatus &&
        matchesSystem &&
        matchesIntent &&
        matchesEu &&
        matchesPurpose &&
        matchesNatsec &&
        matchesSource &&
        matchesCountry
      );
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
      } else if (sortBy === 'damage-desc') {
        return (b.financial_damage_usd || 0) - (a.financial_damage_usd || 0);
      } else if (sortBy === 'confidence-desc') {
        return (b.confidence_scores?.severity || 1.0) - (a.confidence_scores?.severity || 1.0);
      }
      return 0;
    });
  }, [incidents, search, severityFilter, statusFilter, systemFilter, intentFilter, euFilter, purposeFilter, natsecFilter, sourceFilter, countryFilter, sortBy]);

  return (
    <div className="explorer-layout">
      {/* 2-TIER LEFT SIDEBAR FILTERS */}
      <aside className="filters-sidebar">
        <div className="sidebar-header">
          <Filter size={18} />
          <h3>Filter & Sort Controls</h3>
        </div>

        {/* --- TIER 1: PRIMARY FILTERS (ALWAYS VISIBLE ON LEFT) --- */}
        {/* Search */}
        <div className="filter-group">
          <label>Search Query</label>
          <div className="search-input-wrapper">
            <Search className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search entity, title..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        {/* Sort By */}
        <div className="filter-group">
          <label>Sort Incidents</label>
          <div className="select-wrapper">
            <ArrowUpDown size={14} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <select
              className="filter-select"
              style={{ paddingLeft: '2.2rem' }}
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="date-desc">Newest First (Date)</option>
              <option value="date-asc">Oldest First (Date)</option>
              <option value="damage-desc">Highest Damage ($ USD)</option>
              <option value="severity-desc">Highest Severity</option>
              <option value="severity-asc">Lowest Severity</option>
              <option value="entity-asc">Affected Entity (A-Z)</option>
              <option value="entity-desc">Affected Entity (Z-A)</option>
              <option value="confidence-desc">Highest Confidence</option>
            </select>
          </div>
        </div>

        {/* Severity */}
        <div className="filter-group">
          <label>Severity Level</label>
          <select
            className="filter-select"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
          >
            <option value="all">All Severities</option>
            <option value="critical">🔴 Critical Risk</option>
            <option value="high">🟠 High Risk</option>
            <option value="medium">🟡 Medium Risk</option>
            <option value="low">🔵 Low Risk</option>
          </select>
        </div>

        {/* Source Origin Filter */}
        <div className="filter-group">
          <label>Data Provider / Source</label>
          <select
            className="filter-select"
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
          >
            <option value="all">All Data Sources</option>
            <option value="google_news_rss">Google News RSS</option>
            <option value="gdelt">GDELT 2.0 (BigQuery/API)</option>
            <option value="arxiv">ArXiv AI Safety</option>
            <option value="aiid">AI Incident Database</option>
          </select>
        </div>

        {/* Country / Region Filter */}
        <div className="filter-group">
          <label>Geographic Scope / Country</label>
          <select
            className="filter-select"
            value={countryFilter}
            onChange={(e) => setCountryFilter(e.target.value)}
          >
            <option value="all">All Countries / Global</option>
            {uniqueCountries.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        {/* --- TIER 2: ADVANCED REGULATORY TAXONOMY ACCORDION --- */}
        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>
          <button
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            style={{
              width: '100%',
              background: 'transparent',
              border: 'none',
              color: 'var(--accent-cyan)',
              fontSize: '0.8rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              cursor: 'pointer',
              padding: '0.3rem 0'
            }}
          >
            <span>Advanced Regulatory Taxonomy</span>
            {showAdvancedFilters ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {showAdvancedFilters && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem', marginTop: '0.75rem' }}>
              {/* EU AI Act Tier */}
              <div className="filter-group">
                <label>EU AI Act Classification</label>
                <select
                  className="filter-select"
                  value={euFilter}
                  onChange={(e) => setEuFilter(e.target.value)}
                >
                  <option value="all">All EU Risk Tiers</option>
                  <option value="prohibited">Prohibited Risk</option>
                  <option value="high_risk">High Risk</option>
                  <option value="limited_risk">Limited Risk</option>
                  <option value="minimal_risk">Minimal Risk</option>
                </select>
              </div>

              {/* Intent */}
              <div className="filter-group">
                <label>Incident Intent</label>
                <select
                  className="filter-select"
                  value={intentFilter}
                  onChange={(e) => setIntentFilter(e.target.value)}
                >
                  <option value="all">All Intent Types</option>
                  <option value="intentional_misuse">Intentional Misuse</option>
                  <option value="unintentional_failure">Unintentional Failure</option>
                </select>
              </div>

              {/* Primary Purpose */}
              <div className="filter-group">
                <label>Primary System Purpose</label>
                <select
                  className="filter-select"
                  value={purposeFilter}
                  onChange={(e) => setPurposeFilter(e.target.value)}
                >
                  <option value="all">All System Purposes</option>
                  <option value="generative_content">Generative Content</option>
                  <option value="autonomous_mobility">Autonomous Mobility</option>
                  <option value="biometric_surveillance">Biometric Surveillance</option>
                  <option value="financial_fintech">Financial & Fintech</option>
                  <option value="healthcare_medical">Healthcare & Medical</option>
                  <option value="recruitment_hr">Recruitment & HR</option>
                  <option value="defense_national_security">Defense & NatSec</option>
                  <option value="other">Other Domain</option>
                </select>
              </div>

              {/* NatSec Impact */}
              <div className="filter-group">
                <label>NatSec Impact</label>
                <select
                  className="filter-select"
                  value={natsecFilter}
                  onChange={(e) => setNatsecFilter(e.target.value)}
                >
                  <option value="all">All NatSec Statuses</option>
                  <option value="yes">NatSec Impact: Yes</option>
                  <option value="no">NatSec Impact: No</option>
                </select>
              </div>

              {/* Status */}
              <div className="filter-group">
                <label>Verification Status</label>
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
            </div>
          )}
        </div>

        {/* Reset Button */}
        <button
          onClick={handleResetFilters}
          className="button button-outline"
          style={{
            width: '100%',
            marginTop: '0.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.4rem',
            fontSize: '0.8rem'
          }}
        >
          <RotateCcw size={14} /> Reset All Filters
        </button>
      </aside>

      {/* MAIN CONTENT AREA */}
      <section className="explorer-content">
        {/* Active Filter Chips Bar */}
        {activeChips.length > 0 && (
          <div className="active-chips-container">
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Active Filters:</span>
            {activeChips.map((chip, idx) => (
              <span key={idx} className="active-chip" onClick={chip.reset}>
                {chip.label} <X size={12} />
              </span>
            ))}
            <button
              onClick={handleResetFilters}
              style={{ background: 'none', border: 'none', color: '#fca5a5', fontSize: '0.75rem', cursor: 'pointer', marginLeft: 'auto', textDecoration: 'underline' }}
            >
              Clear All
            </button>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          <span>
            Showing <strong style={{ color: 'var(--accent-cyan)' }}>{filteredAndSortedIncidents.length}</strong> of {incidents.length} AI Incidents
          </span>
        </div>

        {/* Grid of Incidents with Left Border Severity Accents */}
        <div className="grid-cards">
          {filteredAndSortedIncidents.map((inc) => (
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
                  {inc.affected_parties && inc.affected_parties.length > 0 && (
                    <span>• {inc.affected_parties[0]}</span>
                  )}
                </div>
                <span className="details-link" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                  Details <ChevronRight size={14} />
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
