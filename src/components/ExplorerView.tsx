import React, { useState, useMemo } from 'react';
import {
  Search,
  ArrowUpDown,
  ShieldAlert,
  Filter,
  RotateCcw,
  DollarSign,
  Globe,
  ChevronDown,
  ChevronUp,
  X,
  ChevronRight,
  Download,
  FileSpreadsheet,
  FileCode,
  LayoutGrid,
  Table as TableIcon
} from 'lucide-react';
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
  const [nistFilter, setNistFilter] = useState<string>('all');
  const [isoFilter, setIsoFilter] = useState<string>('all');
  const [purposeFilter, setPurposeFilter] = useState<string>('all');
  const [natsecFilter, setNatsecFilter] = useState<string>('all');
  const [sourceFilter, setSourceFilter] = useState<string>('all');
  const [countryFilter, setCountryFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('date-desc');

  // Toggle View Mode: 'grid' vs 'table'
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');

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
    setNistFilter('all');
    setIsoFilter('all');
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
    if (nistFilter !== 'all') chips.push({ label: `NIST Function: ${nistFilter}`, reset: () => setNistFilter('all') });
    if (isoFilter !== 'all') chips.push({ label: `ISO 42001: ${isoFilter.replace(/_/g, ' ')}`, reset: () => setIsoFilter('all') });
    if (intentFilter !== 'all') chips.push({ label: `Intent: ${intentFilter.replace(/_/g, ' ')}`, reset: () => setIntentFilter('all') });
    if (purposeFilter !== 'all') chips.push({ label: `Purpose: ${purposeFilter.replace(/_/g, ' ')}`, reset: () => setPurposeFilter('all') });
    if (natsecFilter !== 'all') chips.push({ label: `NatSec: ${natsecFilter}`, reset: () => setNatsecFilter('all') });
    if (statusFilter !== 'all') chips.push({ label: `Status: ${statusFilter}`, reset: () => setStatusFilter('all') });
    return chips;
  }, [search, severityFilter, sourceFilter, countryFilter, euFilter, nistFilter, isoFilter, intentFilter, purposeFilter, natsecFilter, statusFilter]);

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
      const matchesNist = nistFilter === 'all' || (inc.nist_ai_rmf_function || (inc as any).taxonomy?.nist_ai_rmf_function) === nistFilter;
      const matchesIso = isoFilter === 'all' || (inc.iso_42001_category || (inc as any).taxonomy?.iso_42001_category) === isoFilter;
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
        matchesNist &&
        matchesIso &&
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
  }, [incidents, search, severityFilter, statusFilter, systemFilter, intentFilter, euFilter, nistFilter, isoFilter, purposeFilter, natsecFilter, sourceFilter, countryFilter, sortBy]);

  // CSV Export Handler
  const handleExportCSV = () => {
    const headers = [
      'Incident ID',
      'Date',
      'Title',
      'Severity',
      'Financial Damage USD',
      'Country',
      'EU AI Act Tier',
      'NIST AI RMF Function',
      'ISO 42001 Category',
      'Verification Status',
      'Source URL'
    ];

    const rows = filteredAndSortedIncidents.map((inc) => [
      `"${inc.incident_id}"`,
      `"${inc.date || ''}"`,
      `"${(inc.title || '').replace(/"/g, '""')}"`,
      `"${inc.severity || ''}"`,
      inc.financial_damage_usd || 0,
      `"${(inc.geographic_scope || []).join('; ')}"`,
      `"${inc.eu_ai_act_tier || ''}"`,
      `"${inc.nist_ai_rmf_function || (inc as any).taxonomy?.nist_ai_rmf_function || ''}"`,
      `"${inc.iso_42001_category || (inc as any).taxonomy?.iso_42001_category || ''}"`,
      `"${inc.verification_status || ''}"`,
      `"${(inc.source_urls?.[0] || '').replace(/"/g, '""')}"`
    ]);

    const csvString = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
    const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `ai_incidents_export_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // JSON Export Handler
  const handleExportJSON = () => {
    const jsonStr = JSON.stringify(filteredAndSortedIncidents, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `ai_incidents_export_${new Date().toISOString().split('T')[0]}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

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

              {/* NIST AI RMF 1.0 Function */}
              <div className="filter-group">
                <label>NIST AI RMF 1.0 Function</label>
                <select
                  className="filter-select"
                  value={nistFilter}
                  onChange={(e) => setNistFilter(e.target.value)}
                >
                  <option value="all">All NIST Functions</option>
                  <option value="GOVERN">GOVERN (Policy & Oversight)</option>
                  <option value="MAP">MAP (Context & Risk Identification)</option>
                  <option value="MEASURE">MEASURE (Analysis & Evaluation)</option>
                  <option value="MANAGE">MANAGE (Incident Response & Controls)</option>
                </select>
              </div>

              {/* ISO/IEC 42001 Category */}
              <div className="filter-group">
                <label>ISO/IEC 42001 Category</label>
                <select
                  className="filter-select"
                  value={isoFilter}
                  onChange={(e) => setIsoFilter(e.target.value)}
                >
                  <option value="all">All ISO 42001 Categories</option>
                  <option value="Internal_Governance">Internal Governance</option>
                  <option value="Data_&_Resources">Data & Resources</option>
                  <option value="System_Impact">System Impact</option>
                  <option value="Operational_Security">Operational Security</option>
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

        {/* TOOLBAR: Count + Export Buttons + View Mode Switcher */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', background: 'var(--bg-secondary)', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Showing <strong style={{ color: 'var(--accent-cyan)' }}>{filteredAndSortedIncidents.length}</strong> of {incidents.length} AI Incidents
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
            {/* CSV & JSON Export Buttons */}
            <button
              onClick={handleExportCSV}
              className="button button-outline"
              style={{ fontSize: '0.775rem', padding: '0.3rem 0.6rem', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
              title="Download active filtered incidents as CSV"
            >
              <FileSpreadsheet size={14} style={{ color: '#34d399' }} /> Export CSV
            </button>

            <button
              onClick={handleExportJSON}
              className="button button-outline"
              style={{ fontSize: '0.775rem', padding: '0.3rem 0.6rem', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
              title="Download active filtered incidents as JSON"
            >
              <FileCode size={14} style={{ color: 'var(--accent-cyan)' }} /> Export JSON
            </button>

            {/* View Mode Toggle: Grid Cards vs Compact Table */}
            <div style={{ display: 'flex', background: 'rgba(0,0,0,0.3)', padding: '0.15rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
              <button
                onClick={() => setViewMode('grid')}
                style={{
                  border: 'none',
                  background: viewMode === 'grid' ? 'var(--accent-blue)' : 'transparent',
                  color: viewMode === 'grid' ? '#ffffff' : 'var(--text-muted)',
                  fontSize: '0.75rem',
                  padding: '0.25rem 0.5rem',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                  fontWeight: 600
                }}
                title="Cards Grid View"
              >
                <LayoutGrid size={13} /> Cards
              </button>
              <button
                onClick={() => setViewMode('table')}
                style={{
                  border: 'none',
                  background: viewMode === 'table' ? 'var(--accent-blue)' : 'transparent',
                  color: viewMode === 'table' ? '#ffffff' : 'var(--text-muted)',
                  fontSize: '0.75rem',
                  padding: '0.25rem 0.5rem',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                  fontWeight: 600
                }}
                title="Compact Table View"
              >
                <TableIcon size={13} /> Table View
              </button>
            </div>
          </div>
        </div>

        {/* RENDER MODE 1: GRID CARDS VIEW */}
        {viewMode === 'grid' && (
          <div className="grid-cards" style={{ marginTop: '1rem' }}>
            {filteredAndSortedIncidents.map((inc) => {
              const nistVal = inc.nist_ai_rmf_function || (inc as any).taxonomy?.nist_ai_rmf_function;
              return (
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
                    {nistVal && (
                      <span className="badge" style={{ backgroundColor: 'rgba(56, 189, 248, 0.2)', color: '#38bdf8' }}>
                        NIST: {nistVal}
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
              );
            })}
          </div>
        )}

        {/* RENDER MODE 2: HIGH-DENSITY COMPACT TABLE VIEW */}
        {viewMode === 'table' && (
          <div style={{ marginTop: '1rem', overflowX: 'auto', border: '1px solid var(--border-color)', borderRadius: '8px', background: 'var(--bg-secondary)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: 'rgba(0,0,0,0.4)', borderBottom: '1px solid var(--border-color)', color: 'var(--accent-cyan)' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Date</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Incident Title</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Country</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Severity</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Financial Impact ($)</th>
                  <th style={{ padding: '0.75rem 1rem' }}>EU AI Act</th>
                  <th style={{ padding: '0.75rem 1rem' }}>NIST Function</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredAndSortedIncidents.map((inc) => {
                  const nistVal = inc.nist_ai_rmf_function || (inc as any).taxonomy?.nist_ai_rmf_function || 'MAP';
                  const countryStr = (inc.geographic_scope || ['Global']).join(', ');
                  return (
                    <tr
                      key={inc.incident_id}
                      onClick={() => onSelectIncident(inc)}
                      style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', cursor: 'pointer', transition: 'background 0.15s ease' }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(56, 189, 248, 0.08)')}
                      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                    >
                      <td style={{ padding: '0.65rem 1rem', whiteSpace: 'nowrap', color: 'var(--text-muted)', fontSize: '0.8rem' }}>{inc.date}</td>
                      <td style={{ padding: '0.65rem 1rem', fontWeight: 600, color: 'var(--text-main)', maxWidth: '380px' }}>
                        <div style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                          {inc.title}
                        </div>
                      </td>
                      <td style={{ padding: '0.65rem 1rem', whiteSpace: 'nowrap', color: 'var(--text-muted)' }}>{countryStr}</td>
                      <td style={{ padding: '0.65rem 1rem', whiteSpace: 'nowrap' }}>
                        <span className={`severity-badge severity-${inc.severity}`} style={{ fontSize: '0.65rem', padding: '0.1rem 0.35rem', textTransform: 'uppercase', fontWeight: 700 }}>
                          {inc.severity}
                        </span>
                      </td>
                      <td style={{ padding: '0.65rem 1rem', whiteSpace: 'nowrap', color: (inc.financial_damage_usd || 0) > 0 ? '#34d399' : 'var(--text-dim)', fontWeight: 600 }}>
                        {formatFinancialDamage(inc.financial_damage_usd)}
                      </td>
                      <td style={{ padding: '0.65rem 1rem', whiteSpace: 'nowrap', color: 'var(--accent-blue)', fontSize: '0.775rem' }}>
                        {(inc.eu_ai_act_tier || 'limited_risk').replace('_', ' ')}
                      </td>
                      <td style={{ padding: '0.65rem 1rem', whiteSpace: 'nowrap', color: 'var(--accent-purple)', fontSize: '0.775rem', fontWeight: 600 }}>
                        {nistVal}
                      </td>
                      <td style={{ padding: '0.65rem 1rem', textAlign: 'right', whiteSpace: 'nowrap' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                          Open <ChevronRight size={13} />
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
};
