import React, { useState, useMemo } from 'react';
import { FlaskConical, Search, ExternalLink, Cpu, Calendar, ChevronRight, Filter } from 'lucide-react';
import { AIIncident, sanitizeExternalUrl } from '../types/incident';

interface ResearchLabViewProps {
  papers: AIIncident[];
  onSelectPaper: (paper: AIIncident) => void;
}

export const ResearchLabView: React.FC<ResearchLabViewProps> = ({ papers, onSelectPaper }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [failureModeFilter, setFailureModeFilter] = useState('all');
  const [harmDomainFilter, setHarmDomainFilter] = useState('all');
  const [sortBy, setSortBy] = useState<'date-desc' | 'date-asc' | 'title-asc'>('date-desc');

  // Extract unique failure modes and harm domains
  const failureModes = useMemo(() => {
    const set = new Set<string>();
    papers.forEach((p) => {
      if (p.failure_mode) set.add(p.failure_mode);
      else if (p.root_cause_subtype) set.add(p.root_cause_subtype);
    });
    return Array.from(set).sort();
  }, [papers]);

  const harmDomains = useMemo(() => {
    const set = new Set<string>();
    papers.forEach((p) => {
      if (p.harm_domain) set.add(p.harm_domain);
    });
    return Array.from(set).sort();
  }, [papers]);

  // Filter and sort papers
  const filteredPapers = useMemo(() => {
    return papers
      .filter((p) => {
        const query = searchTerm.toLowerCase().trim();
        const matchesSearch =
          !query ||
          p.title.toLowerCase().includes(query) ||
          p.summary.toLowerCase().includes(query) ||
          (p.failure_mode && p.failure_mode.toLowerCase().includes(query)) ||
          (p.affected_parties && p.affected_parties.some((party) => party.toLowerCase().includes(query)));

        const matchesFailureMode =
          failureModeFilter === 'all' ||
          p.failure_mode === failureModeFilter ||
          p.root_cause_subtype === failureModeFilter;

        const matchesHarmDomain = harmDomainFilter === 'all' || p.harm_domain === harmDomainFilter;

        return matchesSearch && matchesFailureMode && matchesHarmDomain;
      })
      .sort((a, b) => {
        if (sortBy === 'date-desc') {
          return (b.date || '').localeCompare(a.date || '');
        } else if (sortBy === 'date-asc') {
          return (a.date || '').localeCompare(b.date || '');
        } else {
          return a.title.localeCompare(b.title);
        }
      });
  }, [papers, searchTerm, failureModeFilter, harmDomainFilter, sortBy]);

  // Telemetry Metrics
  const uniqueFailureCount = useMemo(() => {
    const set = new Set(papers.map((p) => p.failure_mode || p.root_cause_subtype).filter(Boolean));
    return set.size;
  }, [papers]);

  const latestDate = useMemo(() => {
    const sorted = [...papers].sort((a, b) => (b.date || '').localeCompare(a.date || ''));
    return sorted[0]?.date || 'N/A';
  }, [papers]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', paddingBottom: '3rem' }}>
      {/* Hero / Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(56, 189, 248, 0.08) 100%)',
          border: '1px solid rgba(168, 85, 247, 0.3)',
          borderRadius: '12px',
          padding: '1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem'
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem' }}>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.3rem',
                backgroundColor: 'rgba(168, 85, 247, 0.25)',
                color: '#d8b4fe',
                padding: '0.2rem 0.5rem',
                borderRadius: '6px',
                fontSize: '0.75rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}
            >
              <FlaskConical size={13} /> Dedicated Lab Partition
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Separated from Real-World Production Incidents
            </span>
          </div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0, color: 'var(--text-main)' }}>
            AI Safety Research & Vulnerability Lab
          </h2>
          <p style={{ margin: '0.35rem 0 0 0', fontSize: '0.875rem', color: 'var(--text-dim)', maxWidth: '750px', lineHeight: 1.5 }}>
            Academic preprints, red-teaming studies, adversarial jailbreaks, and latent risk evaluations from ArXiv
            (CS.CR, CS.AI, CS.LG, CS.CL). These represent controlled empirical security research and vulnerability disclosures
            prior to operational exploitation.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div
            style={{
              backgroundColor: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '8px',
              padding: '0.75rem 1rem',
              textAlign: 'center'
            }}
          >
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#c084fc' }}>{papers.length}</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Preprints
            </div>
          </div>
          <div
            style={{
              backgroundColor: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '8px',
              padding: '0.75rem 1rem',
              textAlign: 'center'
            }}
          >
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#38bdf8' }}>{uniqueFailureCount}</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Attack Vectors
            </div>
          </div>
          <div
            style={{
              backgroundColor: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '8px',
              padding: '0.75rem 1rem',
              textAlign: 'center'
            }}
          >
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#34d399' }}>$0</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Real-World Loss
            </div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.75rem',
          alignItems: 'center',
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          padding: '0.75rem 1rem'
        }}
      >
        <div style={{ position: 'relative', flex: '1 1 280px' }}>
          <Search
            size={16}
            style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}
          />
          <input
            type="text"
            placeholder="Search papers, attack mechanisms, models (e.g. RAG, Poisoning, Jailbreak)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '0.5rem 0.75rem 0.5rem 2.25rem',
              backgroundColor: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              color: 'var(--text-main)',
              fontSize: '0.85rem'
            }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <Filter size={15} style={{ color: 'var(--text-muted)' }} />
          
          <select
            value={failureModeFilter}
            onChange={(e) => setFailureModeFilter(e.target.value)}
            style={{
              padding: '0.45rem 0.75rem',
              backgroundColor: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              color: 'var(--text-main)',
              fontSize: '0.825rem'
            }}
          >
            <option value="all">All Attack Mechanisms ({papers.length})</option>
            {failureModes.map((fm) => (
              <option key={fm} value={fm}>
                {fm}
              </option>
            ))}
          </select>

          <select
            value={harmDomainFilter}
            onChange={(e) => setHarmDomainFilter(e.target.value)}
            style={{
              padding: '0.45rem 0.75rem',
              backgroundColor: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              color: 'var(--text-main)',
              fontSize: '0.825rem'
            }}
          >
            <option value="all">All Harm Domains</option>
            {harmDomains.map((hd) => (
              <option key={hd} value={hd}>
                {hd.replace(/_/g, ' ')}
              </option>
            ))}
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            style={{
              padding: '0.45rem 0.75rem',
              backgroundColor: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              color: 'var(--text-main)',
              fontSize: '0.825rem'
            }}
          >
            <option value="date-desc">Newest First</option>
            <option value="date-asc">Oldest First</option>
            <option value="title-asc">Title (A-Z)</option>
          </select>
        </div>
      </div>

      {/* Paper Count Subtitle */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
        <span>
          Showing <strong>{filteredPapers.length}</strong> of {papers.length} ArXiv preprints
        </span>
        <span>Latest Paper Date: {latestDate}</span>
      </div>

      {/* Paper Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1rem' }}>
        {filteredPapers.map((paper) => {
          const directArxivUrl = (paper.source_urls || []).find((u) => u.includes('arxiv.org')) || paper.source_urls?.[0] || '#';
          
          return (
            <div
              key={paper.incident_id}
              onClick={() => onSelectPaper(paper)}
              className="paper-card"
              style={{
                backgroundColor: 'var(--bg-secondary)',
                border: '1px solid rgba(168, 85, 247, 0.2)',
                borderRadius: '10px',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                position: 'relative'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'rgba(168, 85, 247, 0.6)';
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 6px 16px rgba(168, 85, 247, 0.15)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'rgba(168, 85, 247, 0.2)';
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <div>
                {/* Badges */}
                <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <span
                    style={{
                      fontSize: '0.675rem',
                      fontWeight: 700,
                      padding: '0.15rem 0.45rem',
                      borderRadius: '4px',
                      backgroundColor: 'rgba(168, 85, 247, 0.2)',
                      color: '#d8b4fe',
                      border: '1px solid rgba(168, 85, 247, 0.35)',
                      textTransform: 'uppercase'
                    }}
                  >
                    ArXiv Preprint
                  </span>
                  <span
                    style={{
                      fontSize: '0.675rem',
                      fontWeight: 600,
                      padding: '0.15rem 0.45rem',
                      borderRadius: '4px',
                      backgroundColor: 'rgba(56, 189, 248, 0.15)',
                      color: '#38bdf8'
                    }}
                  >
                    {paper.severity} Exploit Tier
                  </span>
                  <span
                    style={{
                      fontSize: '0.675rem',
                      fontWeight: 600,
                      padding: '0.15rem 0.45rem',
                      borderRadius: '4px',
                      backgroundColor: 'rgba(251, 191, 36, 0.15)',
                      color: '#fbbf24'
                    }}
                  >
                    🔬 Latent / Lab
                  </span>
                </div>

                {/* Title */}
                <h3
                  style={{
                    fontSize: '1.05rem',
                    fontWeight: 600,
                    margin: '0 0 0.5rem 0',
                    color: 'var(--text-main)',
                    lineHeight: 1.35
                  }}
                >
                  {paper.title}
                </h3>

                {/* Abstract Snippet */}
                <p
                  style={{
                    fontSize: '0.85rem',
                    color: 'var(--text-dim)',
                    lineHeight: 1.45,
                    margin: '0 0 0.85rem 0',
                    display: '-webkit-box',
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden'
                  }}
                >
                  {paper.summary}
                </p>

                {/* Security Attack Vector */}
                {paper.failure_mode && (
                  <div
                    style={{
                      fontSize: '0.775rem',
                      color: 'var(--text-muted)',
                      marginBottom: '0.75rem',
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '0.35rem'
                    }}
                  >
                    <Cpu size={14} style={{ color: '#c084fc', flexShrink: 0, marginTop: '2px' }} />
                    <span style={{ color: 'var(--text-main)', fontWeight: 500 }}>
                      <strong>Vector:</strong> {paper.failure_mode}
                    </span>
                  </div>
                )}

                {/* Evaluated Systems / Models */}
                {paper.affected_parties && paper.affected_parties.length > 0 && (
                  <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
                    {paper.affected_parties.slice(0, 3).map((target, idx) => (
                      <span
                        key={idx}
                        style={{
                          fontSize: '0.7rem',
                          backgroundColor: 'rgba(255, 255, 255, 0.05)',
                          color: 'var(--text-dim)',
                          padding: '0.1rem 0.4rem',
                          borderRadius: '4px'
                        }}
                      >
                        {target}
                      </span>
                    ))}
                    {paper.affected_parties.length > 3 && (
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        +{paper.affected_parties.length - 3} more
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Card Footer */}
              <div
                style={{
                  borderTop: '1px solid rgba(255, 255, 255, 0.06)',
                  paddingTop: '0.75rem',
                  marginTop: '0.5rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '0.775rem',
                  color: 'var(--text-muted)'
                }}
              >
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                  <Calendar size={13} /> {paper.date}
                </span>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  {directArxivUrl && directArxivUrl !== '#' && (
                    <a
                      href={sanitizeExternalUrl(directArxivUrl)}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      style={{
                        color: 'var(--accent-cyan)',
                        textDecoration: 'none',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.2rem',
                        fontWeight: 600
                      }}
                      title="Read on ArXiv.org"
                    >
                      ArXiv PDF <ExternalLink size={12} />
                    </a>
                  )}
                  <span style={{ display: 'inline-flex', alignItems: 'center', color: 'var(--text-main)', fontWeight: 500 }}>
                    Details <ChevronRight size={14} />
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
