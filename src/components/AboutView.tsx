import React from 'react';
import { Info, ShieldAlert, Database, DollarSign, GitMerge, CheckCircle2, ExternalLink, AlertTriangle, BookOpen, Scale, Cpu, Activity, AlertCircle, Layers } from 'lucide-react';

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
                "An event where the development, deployment, or operation of an artificial intelligence system directly causes, or significantly contributes to, real-world physical harm, property damage, mental harm, financial losses, fundamental rights violations, critical infrastructure compromise, public or diplomatic embarrassment arising from AI hallucinations, or unsanctioned autonomous agent behavior."
              </blockquote>
            </div>
          </section>

          {/* Section 2: Multi-Source Ingestion Architecture */}
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
                  <p style={{ fontSize: '0.825rem' }}>Direct BigQuery SQL querying of the global multi-lingual Knowledge Graph dataset for international coverage.</p>
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

          {/* Section 4: Multi-Source Correlation & Incident Deduplication */}
          <section className="detail-section">
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <GitMerge size={18} style={{ color: 'var(--accent-blue)' }} />
              4. Multi-Source Event Correlation & Incident Deduplication
            </h3>
            <div style={{ fontSize: '0.95rem', color: 'var(--text-muted)', lineHeight: 1.75, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <p>
                To prevent multiple media reports or syndicated news feeds from inflating incident statistics, the platform continuously correlates incoming intelligence across all monitored data sources.
              </p>
              <p style={{ background: 'rgba(0,0,0,0.2)', padding: '0.85rem', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.85rem' }}>
                When multiple articles describe the same underlying real-world AI incident—regardless of differing headlines, publication dates, or reporting outlets—the intelligence pipeline automatically merges them into a single canonical incident record. All verified publisher links are consolidated under this primary entry, ensuring clean data integrity, precise incident counts, and non-duplicated financial damage metrics.
              </p>
            </div>
          </section>

          {/* Section 5: Risk Severity Classification Criteria */}
          <section className="detail-section">
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <AlertTriangle size={18} style={{ color: 'var(--accent-orange)' }} />
              5. Severity Level Classification Matrix
            </h3>
            <div style={{ fontSize: '0.95rem', color: 'var(--text-muted)', lineHeight: 1.75, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.25rem' }}>
                <div style={{ background: 'rgba(239, 68, 68, 0.1)', borderLeft: '4px solid var(--accent-red)', padding: '0.85rem 1rem', borderRadius: '6px' }}>
                  <h4 style={{ color: 'var(--accent-red)', fontSize: '0.9rem', marginBottom: '0.25rem' }}>🔴 CRITICAL RISK</h4>
                  <p style={{ fontSize: '0.825rem', color: 'var(--text-main)', margin: 0 }}>
                    Human loss of life/fatalities, multi-million dollar infrastructure breaches (&gt; $10M USD), unauthorized autonomous weapons/national security escapes, or EU AI Act Prohibited Risk violations.
                  </p>
                </div>
                <div style={{ background: 'rgba(249, 115, 22, 0.1)', borderLeft: '4px solid var(--accent-orange)', padding: '0.85rem 1rem', borderRadius: '6px' }}>
                  <h4 style={{ color: 'var(--accent-orange)', fontSize: '0.9rem', marginBottom: '0.25rem' }}>🟠 HIGH RISK</h4>
                  <p style={{ fontSize: '0.825rem', color: 'var(--text-main)', margin: 0 }}>
                    Substantial financial losses ($100K – $10M USD), widespread biometric/privacy breaches, corporate trade secret exfiltration, active deepfake fraud campaigns, or high-risk regulated AI operating without guardrails.
                  </p>
                </div>
                <div style={{ background: 'rgba(234, 179, 8, 0.1)', borderLeft: '4px solid #eab308', padding: '0.85rem 1rem', borderRadius: '6px' }}>
                  <h4 style={{ color: '#eab308', fontSize: '0.9rem', marginBottom: '0.25rem' }}>🟡 MEDIUM RISK</h4>
                  <p style={{ fontSize: '0.825rem', color: 'var(--text-main)', margin: 0 }}>
                    Localized autonomous system malfunctions (e.g. unprompted agent behavior, gym/booking hacks, algorithmic discrimination in recruitment/loans), moderate financial losses (&lt; $100K USD), or disputed safety disclosures.
                  </p>
                </div>
                <div style={{ background: 'rgba(59, 130, 246, 0.1)', borderLeft: '4px solid var(--accent-blue)', padding: '0.85rem 1rem', borderRadius: '6px' }}>
                  <h4 style={{ color: 'var(--accent-cyan)', fontSize: '0.9rem', marginBottom: '0.25rem' }}>🔵 LOW RISK</h4>
                  <p style={{ fontSize: '0.825rem', color: 'var(--text-main)', margin: 0 }}>
                    Minor model alignment deviations, benign hallucination reports without physical or financial harm, controlled academic sandbox vulnerability disclosures, or theoretical latent safety research.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* SECTION 6: COMPREHENSIVE AI RISK & REGULATORY TAXONOMY GLOSSARY */}
          <section className="detail-section">
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', paddingBottom: '0.5rem', borderBottom: '1px solid var(--border-color)' }}>
              <BookOpen size={20} style={{ color: 'var(--accent-cyan)' }} />
              6. Comprehensive AI Risk & Regulatory Taxonomy Glossary
            </h3>
            <p style={{ fontSize: '0.925rem', color: 'var(--text-muted)', lineHeight: 1.6, marginBottom: '1.25rem' }}>
              Every incident ingested into the platform is enriched with structured metadata aligning with statutory regulations (EU AI Act), international standards (NIST AI RMF 1.0, ISO/IEC 42001), and leading academic taxonomies (MIT AI Risk Repository, CSET Georgetown). Below are the formal definitions for all taxonomy fields and their enumerated options:
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              
              {/* 6.1 Lifecycle Phase */}
              <div style={{ background: 'rgba(0,0,0,0.25)', padding: '1.1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <h4 style={{ fontSize: '0.95rem', color: 'var(--accent-cyan)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Activity size={16} /> Lifecycle Phase (`lifecycle_phase`)
                </h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                  Defines the specific stage in the artificial intelligence engineering lifecycle during which the vulnerability, failure, or risk vector originated:
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem', fontSize: '0.825rem' }}>
                  <div>
                    <a href="https://airisk.mit.edu/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • Design & Training (`design_and_training`) <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-dim)', marginTop: '0.15rem' }}>Pre-training dataset selection, architecture design, data poisoning, RLHF/DPO alignment, and parameter tuning.</div>
                  </div>
                  <div>
                    <a href="https://airc.nist.gov/AI_RMF_Knowledge_Base/RMF_Core/Measure" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • Testing & Validation (`testing_and_validation`) <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-dim)', marginTop: '0.15rem' }}>Pre-release red-teaming, safety evaluations, sandbox testing, benchmark execution, and adversarial robustness audits.</div>
                  </div>
                  <div>
                    <a href="https://oecd.ai/en/classification" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • Deployment & Integration (`deployment_and_integration`) <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-dim)', marginTop: '0.15rem' }}>Rollout into live enterprise IT environments, API embedding, cloud infrastructure integration, and client software delivery.</div>
                  </div>
                  <div>
                    <a href="https://airc.nist.gov/AI_RMF_Knowledge_Base/RMF_Core/Manage" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • Operation & Monitoring (`operation_and_monitoring`) <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-dim)', marginTop: '0.15rem' }}>Active production deployment, telemetry logging, real-world user interactions, performance tracking, and data drift detection.</div>
                  </div>
                  <div style={{ gridColumn: '1 / -1' }}>
                    <a href="https://www.iso.org/standard/81230.html" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • Decommissioning (`decommissioning`) <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-dim)', marginTop: '0.15rem' }}>Model retirement, emergency kill-switch activation, legacy API deprecation, or statutory product recall.</div>
                  </div>
                </div>
              </div>

              {/* 6.2 EU AI Act Risk Tiers */}
              <div style={{ background: 'rgba(0,0,0,0.25)', padding: '1.1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <h4 style={{ fontSize: '0.95rem', color: '#38bdf8', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Scale size={16} /> EU AI Act Regulatory Risk Tiers (Regulation EU 2024/1689) (`eu_ai_act_tier`)
                </h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                  Categorizes systems according to statutory risk tiers mandated by the European Union Artificial Intelligence Act:
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.825rem' }}>
                  <div style={{ background: 'rgba(239, 68, 68, 0.08)', padding: '0.6rem', borderRadius: '4px', borderLeft: '3px solid var(--accent-red)' }}>
                    <a href="https://artificialintelligenceact.eu/article/5/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-red)', fontWeight: 700, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      Prohibited Risk (`prohibited`) — Article 5 <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-main)', marginTop: '0.15rem' }}>Banned AI practices violating fundamental rights: social scoring, cognitive behavioral manipulation, untargeted facial recognition scraping, emotion recognition in workplaces/schools, and predictive policing.</div>
                  </div>
                  <div style={{ background: 'rgba(249, 115, 22, 0.08)', padding: '0.6rem', borderRadius: '4px', borderLeft: '3px solid var(--accent-orange)' }}>
                    <a href="https://artificialintelligenceact.eu/article/6/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-orange)', fontWeight: 700, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      High Risk (`high_risk`) — Article 6 & Annex III <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-main)', marginTop: '0.15rem' }}>Mandatory statutory compliance systems: critical infrastructure components, medical software, recruitment/HR screening, credit scoring, law enforcement risk assessments, and biometric categorization.</div>
                  </div>
                  <div style={{ background: 'rgba(234, 179, 8, 0.08)', padding: '0.6rem', borderRadius: '4px', borderLeft: '3px solid #eab308' }}>
                    <a href="https://artificialintelligenceact.eu/article/50/" target="_blank" rel="noopener noreferrer" style={{ color: '#eab308', fontWeight: 700, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      Limited Risk / Transparency (`limited_risk`) — Article 50 <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-main)', marginTop: '0.15rem' }}>Systems subject to mandatory transparency notifications: AI chatbots, deepfake audio/video generation, and synthetic text generators interacting with humans.</div>
                  </div>
                  <div style={{ background: 'rgba(59, 130, 246, 0.08)', padding: '0.6rem', borderRadius: '4px', borderLeft: '3px solid var(--accent-blue)' }}>
                    <a href="https://artificialintelligenceact.eu/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-cyan)', fontWeight: 700, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      Minimal / Unregulated Risk (`minimal_risk`) <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-main)', marginTop: '0.15rem' }}>Low-risk applications requiring no mandatory statutory compliance (e.g. AI video game NPCs, spam filters, recommendation engines without systemic risk).</div>
                  </div>
                </div>
              </div>

              {/* 6.3 NIST AI RMF & ISO 42001 */}
              <div style={{ background: 'rgba(0,0,0,0.25)', padding: '1.1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <h4 style={{ fontSize: '0.95rem', color: '#a78bfa', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Layers size={16} /> NIST AI RMF 1.0 & ISO/IEC 42001 Framework Categories
                </h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                  Maps risk vectors directly to the four core functions of the US NIST AI Risk Management Framework 1.0 and ISO/IEC 42001 AI Management Systems (AIMS):
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem', fontSize: '0.825rem' }}>
                  <div>
                    <a href="https://airc.nist.gov/AI_RMF_Knowledge_Base/RMF_Core/Govern" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-purple)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • NIST GOVERN (`GOVERN`) <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-dim)', marginTop: '0.15rem' }}>Organizational policies, executive accountability, risk culture, ethical alignment, and governance compliance.</div>
                  </div>
                  <div>
                    <a href="https://airc.nist.gov/AI_RMF_Knowledge_Base/RMF_Core/Map" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-purple)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • NIST MAP (`MAP`) <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-dim)', marginTop: '0.15rem' }}>Contextualizing capabilities, identifying impact vectors, mapping interdependencies, and defining system boundaries.</div>
                  </div>
                  <div>
                    <a href="https://airc.nist.gov/AI_RMF_Knowledge_Base/RMF_Core/Measure" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-purple)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • NIST MEASURE (`MEASURE`) <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-dim)', marginTop: '0.15rem' }}>Quantitative testing, metrics evaluation, safety benchmarking, bias auditing, and red-teaming measurement.</div>
                  </div>
                  <div>
                    <a href="https://airc.nist.gov/AI_RMF_Knowledge_Base/RMF_Core/Manage" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-purple)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • NIST MANAGE (`MANAGE`) <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-dim)', marginTop: '0.15rem' }}>Continuous risk response, threat mitigation, emergency fallback procedures, and post-incident containment.</div>
                  </div>
                  <div style={{ gridColumn: '1 / -1', marginTop: '0.25rem', paddingTop: '0.5rem', borderTop: '1px solid rgba(255,255,255,0.07)' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>ISO/IEC 42001 AIMS Categories (`iso_42001_category`): </span>
                    <a href="https://www.iso.org/standard/81230.html" target="_blank" rel="noopener noreferrer" style={{ color: '#34d399', textDecoration: 'none' }}>
                      Internal_Governance <ExternalLink size={9} />
                    </a> (Leadership & Policy), <a href="https://www.iso.org/committee/6794475.html" target="_blank" rel="noopener noreferrer" style={{ color: '#34d399', textDecoration: 'none' }}>
                      Data_&_Resources <ExternalLink size={9} />
                    </a> (Data Provenance & Compute), <a href="https://www.iso.org/standard/81230.html" target="_blank" rel="noopener noreferrer" style={{ color: '#34d399', textDecoration: 'none' }}>
                      System_Impact <ExternalLink size={9} />
                    </a> (Impact Assessment), <a href="https://www.iso.org/standard/81230.html" target="_blank" rel="noopener noreferrer" style={{ color: '#34d399', textDecoration: 'none' }}>
                      Operational_Security <ExternalLink size={9} />
                    </a> (Access & Model Security).
                  </div>
                </div>
              </div>

              {/* 6.4 System Classification Architecture Types */}
              <div style={{ background: 'rgba(0,0,0,0.25)', padding: '1.1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <h4 style={{ fontSize: '0.95rem', color: '#f472b6', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Cpu size={16} /> System Classification & Architecture Types (`system_classification`)
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem', fontSize: '0.825rem' }}>
                  <div>
                    <a href="https://artificialintelligenceact.eu/article/6/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • High-Risk Regulated (`high_risk_regulated`) <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-dim)', marginTop: '0.15rem' }}>Mission-critical algorithms subject to formal statutory compliance and conformity audits.</div>
                  </div>
                  <div>
                    <a href="https://artificialintelligenceact.eu/article/50/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • General-Purpose Model (`general_purpose_model`) <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-dim)', marginTop: '0.15rem' }}>Large foundation models (LLMs, LMMs) featuring broad multi-modal capabilities across diverse domains.</div>
                  </div>
                  <div>
                    <a href="https://airisk.mit.edu/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • Autonomous Agent (`autonomous_agent`) <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-dim)', marginTop: '0.15rem' }}>Agentic AI systems possessing autonomous tool execution, environment interaction, and multi-step goal planning.</div>
                  </div>
                  <div>
                    <a href="https://artificialintelligenceact.eu/article/5/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • Biometric Identification (`biometric_identification`) <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-dim)', marginTop: '0.15rem' }}>Remote biometric identification, facial recognition, gait analysis, or emotion recognition engines.</div>
                  </div>
                  <div>
                    <a href="https://artificialintelligenceact.eu/article/6/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • Critical Infrastructure Component (`critical_infrastructure_component`) <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-dim)', marginTop: '0.15rem' }}>AI integrated into energy distribution, traffic management, water networks, or banking clearinghouses.</div>
                  </div>
                  <div>
                    <a href="https://airisk.mit.edu/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • Dual-Use Security (`dual_use_security`) <ExternalLink size={10} />
                    </a>
                    <div style={{ color: 'var(--text-dim)', marginTop: '0.15rem' }}>Models with latent capabilities for offensive cyber warfare, chemical/biological weapon design, or exploitation.</div>
                  </div>
                </div>
              </div>

              {/* 6.5 Intent Vectors & Primary Purpose */}
              <div style={{ background: 'rgba(0,0,0,0.25)', padding: '1.1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <h4 style={{ fontSize: '0.95rem', color: '#fb7185', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <AlertCircle size={16} /> Intent Vectors (`intent`) & Primary Purpose (`primary_purpose`)
                </h4>
                <div style={{ fontSize: '0.825rem', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                  <div>
                    <a href="https://cset.georgetown.edu/publication/a-taxonomy-of-ai-incidents/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-red)', fontWeight: 700, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      Intentional Misuse (`intentional_misuse`) <ExternalLink size={10} />
                    </a>: Malicious human exploitation, deliberate prompt injection attacks, jailbreaking, deepfake fraud campaigns, or unauthorized surveillance.
                  </div>
                  <div>
                    <a href="https://cset.georgetown.edu/publication/a-taxonomy-of-ai-incidents/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-cyan)', fontWeight: 700, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      Unintentional Failure (`unintentional_failure`) <ExternalLink size={10} />
                    </a>: Systemic model hallucination, out-of-distribution failure, emergent unintended behavior, data drift, or software integration glitches.
                  </div>
                  <div style={{ marginTop: '0.25rem', color: 'var(--text-muted)' }}>
                    <strong style={{ color: 'var(--text-main)' }}>Primary Purpose Categories:</strong> Generative Content (`generative_content`), Autonomous Mobility (`autonomous_mobility`), Biometric Surveillance (`biometric_surveillance`), Financial & FinTech (`financial_fintech`), Healthcare & Medical (`healthcare_medical`), Recruitment & HR (`recruitment_hr`), Defense & National Security (`defense_national_security`), Content Recommendation (`content_recommendation`).
                  </div>
                </div>
              </div>

              {/* 6.6 Harm Domains & Harm Types */}
              <div style={{ background: 'rgba(0,0,0,0.25)', padding: '1.1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <h4 style={{ fontSize: '0.95rem', color: '#f87171', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <ShieldAlert size={16} /> Harm Domains (`harm_domain`) & Harm Types (`harm_type`)
                </h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                  Aligned with CSET Georgetown and MIT AI Risk Repository harm taxonomies:
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.825rem' }}>
                  <div>
                    <a href="https://cset.georgetown.edu/publication/a-taxonomy-of-ai-incidents/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • Persons - Physical (`persons_physical`) <ExternalLink size={10} />
                    </a>: Fatalities, bodily injury, or workplace safety incidents.
                  </div>
                  <div>
                    <a href="https://cset.georgetown.edu/publication/a-taxonomy-of-ai-incidents/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • Persons - Mental (`persons_mental`) <ExternalLink size={10} />
                    </a>: Psychological trauma, coercion, or suicide encouragement.
                  </div>
                  <div>
                    <a href="https://artificialintelligenceact.eu/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • Persons - Rights (`persons_rights`) <ExternalLink size={10} />
                    </a>: Civil liberties, non-discrimination, privacy, and due process.
                  </div>
                  <div>
                    <a href="https://cset.georgetown.edu/publication/a-taxonomy-of-ai-incidents/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • Property (`property`) <ExternalLink size={10} />
                    </a>: Physical property damage or corporate financial asset loss.
                  </div>
                  <div>
                    <a href="https://oecd.ai/en/classification" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • Systemic Integrity (`systemic_integrity`) <ExternalLink size={10} />
                    </a>: IT network downtime, financial market instability, or supply chain disruption.
                  </div>
                  <div>
                    <a href="https://cset.georgetown.edu/publication/a-taxonomy-of-ai-incidents/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      • Societal (`societal`) <ExternalLink size={10} />
                    </a>: Erosion of democratic processes, mass misinformation, or institutional destabilization.
                  </div>
                  <div style={{ gridColumn: '1 / -1', marginTop: '0.25rem', paddingTop: '0.5rem', borderTop: '1px solid rgba(255,255,255,0.07)', color: 'var(--text-muted)' }}>
                    <strong style={{ color: 'var(--text-main)' }}>Harm Type Sub-Classifications:</strong> Discrimination & Bias (`discrimination_bias`), Privacy Breach (`privacy_breach`), Physical Safety (`physical_safety`), Misinformation (`misinformation`), Economic & Labor (`economic_labor`), Copyright & IP (`copyright_ip`), Psychological Harm (`psychological_harm`), National Security (`national_security`).
                  </div>
                </div>
              </div>

              {/* 6.7 Root Cause Categories */}
              <div style={{ background: 'rgba(0,0,0,0.25)', padding: '1.1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <h4 style={{ fontSize: '0.95rem', color: '#38bdf8', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Database size={16} /> Root Cause Categories (`root_cause_category`) & Subtypes
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.825rem' }}>
                  <div><strong style={{ color: 'var(--text-main)' }}>• Data (`data`):</strong> Dataset poisoning, training bias, data drift, or insufficient validation sampling.</div>
                  <div><strong style={{ color: 'var(--text-main)' }}>• Model (`model`):</strong> Architectural flaw, hallucination tendency, alignment deficit, or emergent unexpected behavior.</div>
                  <div><strong style={{ color: 'var(--text-main)' }}>• Human (`human`):</strong> Operator oversight absence, user error, flawed prompt design, or automation bias.</div>
                  <div><strong style={{ color: 'var(--text-main)' }}>• Governance (`governance`):</strong> Inadequate safety policies, missing pre-release testing, or absent risk management controls.</div>
                  <div><strong style={{ color: 'var(--text-main)' }}>• External (`external`):</strong> Adversarial prompt injection, jailbreak payload, third-party API attack, or cyber intrusion.</div>
                  <div><strong style={{ color: 'var(--text-main)' }}>• Undetermined (`undetermined`):</strong> Under ongoing forensic investigation.</div>
                </div>
              </div>

            </div>
          </section>

        </div>

        {/* RIGHT SIDEBAR: TAXONOMY FRAMEWORKS & DISCLAIMER */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', position: 'sticky', top: '5rem' }}>
          
          <div className="detail-section">
            <h4 style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>
              Authoritative Framework Links
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.85rem' }}>
              <a href="https://artificialintelligenceact.eu/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle2 size={14} style={{ color: '#34d399' }} /> EU AI Act (Art. 5, 6, 50, 73) <ExternalLink size={12} style={{ color: 'var(--text-dim)' }} />
              </a>
              <a href="https://airc.nist.gov/AI_RMF_Knowledge_Base/RMF_Core" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle2 size={14} style={{ color: '#34d399' }} /> NIST AI RMF 1.0 Functions <ExternalLink size={12} style={{ color: 'var(--text-dim)' }} />
              </a>
              <a href="https://www.iso.org/standard/81230.html" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle2 size={14} style={{ color: '#34d399' }} /> ISO/IEC 42001:2023 AIMS <ExternalLink size={12} style={{ color: 'var(--text-dim)' }} />
              </a>
              <a href="https://airisk.mit.edu/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle2 size={14} style={{ color: '#34d399' }} /> MIT AI Risk Repository <ExternalLink size={12} style={{ color: 'var(--text-dim)' }} />
              </a>
              <a href="https://cset.georgetown.edu/publication/a-taxonomy-of-ai-incidents/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle2 size={14} style={{ color: '#34d399' }} /> CSET Georgetown Harm Framework <ExternalLink size={12} style={{ color: 'var(--text-dim)' }} />
              </a>
              <a href="https://oecd.ai/en/classification" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-main)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle2 size={14} style={{ color: '#34d399' }} /> OECD AI System Taxonomy <ExternalLink size={12} style={{ color: 'var(--text-dim)' }} />
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
