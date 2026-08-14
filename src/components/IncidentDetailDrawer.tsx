import React from 'react';
import { X, ExternalLink, ShieldCheck, AlertTriangle, GitFork, ShieldAlert, Zap, Layers, DollarSign, ChevronLeft, ChevronRight } from 'lucide-react';
import { AIIncident, GraphEdge, formatFinancialDamage } from '../types/incident';

interface IncidentDetailDrawerProps {
  incident: AIIncident | null;
  edges: GraphEdge[];
  allIncidents: AIIncident[];
  onClose: () => void;
  onSelectRelated: (incident: AIIncident) => void;
}

export const IncidentDetailDrawer: React.FC<IncidentDetailDrawerProps> = ({
  incident,
  edges,
  allIncidents,
  onClose,
  onSelectRelated
}) => {
  if (!incident) return null;

  const incidentMap = new Map(allIncidents.map((i) => [i.incident_id, i]));
  const currentIndex = allIncidents.findIndex((i) => i.incident_id === incident.incident_id);

  const handlePrev = () => {
    if (currentIndex > 0) {
      onSelectRelated(allIncidents[currentIndex - 1]);
    }
  };

  const handleNext = () => {
    if (currentIndex >= 0 && currentIndex < allIncidents.length - 1) {
      onSelectRelated(allIncidents[currentIndex + 1]);
    }
  };

  const connectedEdges = edges.filter(
    (e) => e.source_id === incident.incident_id || e.target_id === incident.incident_id
  );

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        {/* Drawer Header with Stepper Buttons */}
        <div className="drawer-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontFamily: 'monospace', fontSize: '0.85rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>
              {incident.incident_id}
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              ({currentIndex + 1} of {allIncidents.length})
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {/* Feed Navigation Buttons */}
            <button
              onClick={handlePrev}
              disabled={currentIndex <= 0}
              className="button button-outline"
              style={{ padding: '0.25rem 0.5rem', opacity: currentIndex <= 0 ? 0.4 : 1 }}
              title="Previous Incident"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={handleNext}
              disabled={currentIndex >= allIncidents.length - 1}
              className="button button-outline"
              style={{ padding: '0.25rem 0.5rem', opacity: currentIndex >= allIncidents.length - 1 ? 0.4 : 1 }}
              title="Next Incident"
            >
              <ChevronRight size={16} />
            </button>

            <button
              onClick={onClose}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', marginLeft: '0.5rem' }}
            >
              <X size={22} />
            </button>
          </div>
        </div>

        {/* Drawer Body */}
        <div className="drawer-body">
          <div>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
              <span className={`badge badge-${incident.severity}`}>{incident.severity}</span>
              <span className={`badge badge-${incident.verification_status}`}>{incident.verification_status}</span>
              <span className="badge" style={{ backgroundColor: 'rgba(168, 85, 247, 0.2)', color: '#d8b4fe' }}>
                Src: {(incident.source_type || 'google_news_rss').replace(/_/g, ' ')}
              </span>
              {incident.financial_damage_usd ? incident.financial_damage_usd > 0 ? (
                <span className="badge" style={{ backgroundColor: 'rgba(16, 185, 129, 0.2)', color: '#34d399', display: 'inline-flex', alignItems: 'center', gap: '0.2rem', fontWeight: 700 }}>
                  <DollarSign size={12} /> Est. Damage: {formatFinancialDamage(incident.financial_damage_usd)}
                </span>
              ) : null : null}
              {incident.eu_ai_act_tier && (
                <span className="badge" style={{ backgroundColor: 'rgba(59, 130, 246, 0.2)', color: '#93c5fd' }}>
                  EU: {incident.eu_ai_act_tier.replace('_', ' ')}
                </span>
              )}
              {incident.natsec_impact && (
                <span className="badge" style={{ backgroundColor: 'rgba(239, 68, 68, 0.25)', color: '#fca5a5', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                  <ShieldAlert size={12} /> NatSec Impact
                </span>
              )}
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, lineHeight: 1.3 }}>{incident.title}</h2>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Reported Date: {incident.date}</span>
          </div>

          <div className="detail-section">
            <h4>Executive Summary</h4>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-main)', lineHeight: 1.5 }}>{incident.summary}</p>
          </div>

          {incident.failure_mode && (
            <div className="detail-section" style={{ borderColor: 'rgba(239, 68, 68, 0.3)' }}>
              <h4 style={{ color: '#fca5a5', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <AlertTriangle size={14} /> Causal Failure Mode & Mechanism
              </h4>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-main)', lineHeight: 1.5 }}>{incident.failure_mode}</p>
            </div>
          )}

          <div className="detail-section">
            <h4>MIT AI Risk & Regulatory Taxonomy</h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.825rem' }}>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Lifecycle Phase:</span>
                <p style={{ fontWeight: 500 }}>{incident.lifecycle_phase?.replace(/_/g, ' ')}</p>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>System Classification:</span>
                <p style={{ fontWeight: 500 }}>{incident.system_classification?.replace(/_/g, ' ')}</p>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Intent:</span>
                <p style={{ fontWeight: 500 }}>{incident.intent?.replace(/_/g, ' ') || 'N/A'}</p>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Primary Purpose:</span>
                <p style={{ fontWeight: 500 }}>{incident.primary_purpose?.replace(/_/g, ' ') || 'N/A'}</p>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Harm Domain:</span>
                <p style={{ fontWeight: 500 }}>{incident.harm_domain?.replace(/_/g, ' ')}</p>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Harm Type:</span>
                <p style={{ fontWeight: 500 }}>{incident.harm_type?.replace(/_/g, ' ') || 'N/A'}</p>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Root Cause Category:</span>
                <p style={{ fontWeight: 500 }}>{incident.root_cause_category}</p>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Subtype:</span>
                <p style={{ fontWeight: 500 }}>{incident.root_cause_subtype || 'N/A'}</p>
              </div>
            </div>
          </div>

          {incident.affected_parties && incident.affected_parties.length > 0 && (
            <div className="detail-section">
              <h4>Affected Entities & Systems</h4>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                {incident.affected_parties.map((party, idx) => (
                  <span
                    key={idx}
                    style={{
                      background: 'rgba(59, 130, 246, 0.15)',
                      color: 'var(--accent-cyan)',
                      padding: '0.2rem 0.5rem',
                      borderRadius: '4px',
                      fontSize: '0.8rem'
                    }}
                  >
                    {party}
                  </span>
                ))}
              </div>
            </div>
          )}

          {connectedEdges.length > 0 && (
            <div className="detail-section">
              <h4>Knowledge Graph Causal Connections ({connectedEdges.length})</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {connectedEdges.map((edge) => {
                  const relatedId = edge.source_id === incident.incident_id ? edge.target_id : edge.source_id;
                  const relatedInc = incidentMap.get(relatedId);
                  if (!relatedInc) return null;

                  return (
                    <div
                      key={edge.edge_id}
                      onClick={() => onSelectRelated(relatedInc)}
                      style={{
                        padding: '0.5rem',
                        background: 'rgba(255, 255, 255, 0.03)',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <span className="badge" style={{ backgroundColor: 'rgba(139, 92, 246, 0.2)', color: '#c084fc' }}>
                          {edge.relation_type}
                        </span>
                        <p style={{ fontSize: '0.85rem', fontWeight: 500, marginTop: '0.2rem' }}>{relatedInc.title}</p>
                      </div>
                      <ChevronRight size={16} style={{ color: 'var(--text-muted)' }} />
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {incident.source_urls && incident.source_urls.length > 0 && (
            <div className="detail-section">
              <h4>Source Evidence Links</h4>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {incident.source_urls.map((url, idx) => (
                  <li key={idx}>
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        color: 'var(--accent-blue)',
                        fontSize: '0.825rem',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                        wordBreak: 'break-all'
                      }}
                    >
                      <ExternalLink size={12} /> {url}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
