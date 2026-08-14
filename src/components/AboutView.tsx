import React from 'react';
import { Info, ShieldAlert, Database, DollarSign, GitMerge, CheckCircle2, ExternalLink } from 'lucide-react';

export const AboutView: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Top Header Banner */}
      <div className="detail-section" style={{ background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.9) 100%)', borderLeft: '4px solid var(--accent-blue)', padding: '2rem', borderRadius: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
          <Info size={26} style={{ color: 'var(--accent-cyan)' }} />
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-main)' }}>
            About & Methodology — Global AI Incident Monitor
          </h2>
        </div>
        <p style={{ fontSize: '1.025rem', color: '#e2e8f0', lineHeight: 1.7, maxWidth: '75ch' }}>
          The <strong>Global AI Incident Monitor (AIIM)</strong> is a specialized analytics platform providing real-time multi-source intelligence on AI Incidents, systemic risks, security breaches, legal actions, and regulatory enforcement.
        </p>
      </div>

      {/* Main 2-Column Methodology Content */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 340px', gap: '1.5rem', alignItems: 'start' }}>
        
        {/* LEFT MAIN COLUMN: DETAILED METHODOLOGY SECTIONS */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Section 1: Definition of an AI Incident */}
          <section className="detail-section">
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <ShieldAlert size={18} style={{ color: 'var(--accent-red)' }} />
              1. Definition of an "AI Incident"
            </h3>
            <div style={{ fontSize: '0.95rem', color: 'var(--text-muted)', lineHeight: 1.75, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <p>
                In alignment with international frameworks, an <em>AI Incident</em> is formally defined as:
              </p>
              <blockquote style={{ background: 'rgba(0,0,0,0.3)', borderLeft: '3px solid var(--accent-cyan)', padding: '0.85rem 1.25rem', borderRadius: '4px', color: 'var(--text-main)', fontStyle: 'italic' }}>
                "An event where the development, deployment, or operation of an artificial intelligence system directly causes, or significantly contributes to, real-world physical harm, property damage, mental harm, financial losses, fundamental rights violations, critical infrastructure compromise, or unsanctioned autonomous agent behavior."
              </blockquote>
            </div>
          </section>

          {/* Section 2: Data Sources & Ingestion Pipeline */}
          <section className="detail-section">
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <Database size={18} style={{ color: 'var(--accent-purple)' }} />
              2. Multi-Source Ingestion Architecture
            </h3>
            <div style={{ fontSize: '0.95rem', color: 'var(--text-muted)', lineHeight: 1.75, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <p>The platform aggregates news intelligence and research data from four primary channels:</p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '0.5rem' }}>
                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <h4 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>
                    <a href="https://news.google.com/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-cyan)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      Google News RSS <ExternalLink size={12} />
                    </a>
                  </h4>
                  <p style={{ fontSize: '0.825rem' }}>Continuous automated scanning of global news publishers, breaking tech media, and court press releases.</p>
                </div>
                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <h4 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>
                    <a href="https://www.gdeltproject.org/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-purple)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      GDELT 2.0 Project <ExternalLink size={12} />
                    </a>
                  </h4>
                  <p style={{ fontSize: '0.825rem' }}>Direct SQL querying of the global multi-lingual Knowledge Graph dataset for international coverage.</p>
                </div>
                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <h4 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>
                    <a href="https://arxiv.org/" target="_blank" rel="noopener noreferrer" style={{ color: '#34d399', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      ArXiv AI Research <ExternalLink size={12} />
                    </a>
                  </h4>
                  <p style={{ fontSize: '0.825rem' }}>Research papers evaluating sandbox escapes, model alignment failures, and vulnerability disclosures.</p>
                </div>
                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <h4 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>
                    <a href="https://incidentdatabase.ai/" target="_blank" rel="noopener noreferrer" style={{ color: '#fdba74', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      AI Incident Database (AIID) <ExternalLink size={12} />
                    </a>
                  </h4>
                  <p style={{ fontSize: '0.825rem' }}>Crowdsourced historical incident taxonomy and cross-reference validation IDs.</p>
                </div>
              </div>
            </div>
          </section>

          {/* Section 3: Financial Damage Valuation Methodology */}
          <section className="detail-section">
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <DollarSign size={18} style={{ color: '#34d399' }} />
              3. Financial Impact Valuation Methodology (`financial_damage_usd`)
            </h3>
            <div style={{ fontSize: '0.95rem', color: 'var(--text-muted)', lineHeight: 1.75, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <p>
                To quantify economic risk, Gemini 3.6 Flash evaluates the full text of each incident according to three financial assessment tiers:
              </p>
              <ul style={{ paddingLeft: '1.25rem', margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <li>
                  <strong style={{ color: 'var(--text-main)' }}>Explicit Figures (Fines, Lawsuits & Fraud)</strong>: Direct conversion of court settlements, SEC stock loss claims, GDPR/EU fines, and verified crypto fraud theft amounts.
                </li>
                <li>
                  <strong style={{ color: 'var(--text-main)' }}>VSL Benchmark (Value of a Statistical Life)</strong>: For incidents involving human loss of life or fatal physical harm, Gemini applies the standard US DOT/EPA benchmark of <strong>$12,500,000 USD ($12.5M) per fatality</strong> plus legal liabilities.
                </li>
                <li>
                  <strong style={{ color: 'var(--text-main)' }}>Model-Based Risk Estimation</strong>: For autonomous system escapes and IT security intrusions, costs are estimated based on incident response fees, forensic audits, and downtime.
                </li>
              </ul>
            </div>
          </section>

          {/* Section 4: Deduplication Engine */}
          <section className="detail-section">
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <GitMerge size={18} style={{ color: 'var(--accent-blue)' }} />
              4. Deduplication & Cross-Date Data Integrity Engine
            </h3>
            <div style={{ fontSize: '0.95rem', color: 'var(--text-muted)', lineHeight: 1.75, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <p>
                To prevent duplicate news reports from inflating incident counts, the platform employs a dual-stage <strong>Fuzzy SequenceMatcher & Word-Jaccard Deduplicator</strong>:
              </p>
              <p style={{ background: 'rgba(0,0,0,0.2)', padding: '0.85rem', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.85rem' }}>
                When multiple articles describe the same underlying event across different dates, the pipeline automatically merges their source URLs into a single canonical record while preserving the earliest date and highest severity score.
              </p>
            </div>
          </section>

        </div>

        {/* RIGHT SIDEBAR: TAXONOMY FRAMEWORKS & DISCLAIMER */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', position: 'sticky', top: '5rem' }}>
          
          <div className="detail-section">
            <h4 style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>
              Taxonomy Frameworks
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.85rem' }}>
              <a href="https://artificialintelligenceact.eu/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle2 size={14} style={{ color: '#34d399' }} /> EU AI Act (Art. 73) Tiers <ExternalLink size={12} style={{ color: 'var(--text-dim)' }} />
              </a>
              <a href="https://cset.georgetown.edu/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle2 size={14} style={{ color: '#34d399' }} /> CSET Harm Domains <ExternalLink size={12} style={{ color: 'var(--text-dim)' }} />
              </a>
              <a href="https://airisk.mit.edu/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle2 size={14} style={{ color: '#34d399' }} /> MIT AI Risk Repository <ExternalLink size={12} style={{ color: 'var(--text-dim)' }} />
              </a>
              <a href="https://oecd.ai/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle2 size={14} style={{ color: '#34d399' }} /> OECD AI Taxonomy <ExternalLink size={12} style={{ color: 'var(--text-dim)' }} />
              </a>
            </div>
          </div>

          <div className="detail-section" style={{ background: 'rgba(239, 68, 68, 0.08)', borderColor: 'rgba(239, 68, 68, 0.25)' }}>
            <h4 style={{ fontSize: '0.75rem', color: '#fca5a5', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.3rem' }}>
              Research Disclaimer
            </h4>
            <p style={{ fontSize: '0.775rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
              Financial damage figures and taxonomy classifications are generated via automated analysis of open-source intelligence. Values represent estimated economic indicators for risk assessment purposes.
            </p>
          </div>

        </div>

      </div>
    </div>
  );
};
