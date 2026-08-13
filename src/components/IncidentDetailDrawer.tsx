import React from 'react';
import { X, ExternalLink, ShieldCheck, AlertTriangle, GitFork, ShieldAlert, Zap, Layers } from 'lucide-react';
import { AIIncident, GraphEdge } from '../types/incident';

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

  const connectedEdges = edges.filter(
    (e) => e.source_id === incident.incident_id || e.target_id === incident.incident_id
  );

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-drawer" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--accent-cyan)' }}>
            {incident.incident_id}
          </span>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
          >
            <X size={22} />
          </button>
        </div>

        <div>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
            <span className={`badge badge-${incident.severity}`}>{incident.severity}</span>
            <span className={`badge badge-${incident.verification_status}`}>{incident.verification_status}</span>
            <span className="badge" style={{ backgroundColor: 'rgba(168, 85, 247, 0.2)', color: '#d8b4fe' }}>
              Src: {(incident.source_type || 'google_news_rss').replace(/_/g, ' ')}
            </span>
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
              <AlertTriangle size={14} /> Causal Failure Mode (Narrative)
            </h4>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-main)' }}>{incident.failure_mode}</p>
          </div>
        )}

        {/* MIT & AIID Extended Classification */}
        {(incident.intent || incident.primary_purpose || incident.harm_type) && (
          <div className="detail-section" style={{ borderColor: 'rgba(56, 189, 248, 0.3)' }}>
            <h4 style={{ color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Layers size={14} /> MIT AI Risk & AIID Taxonomy Extensions
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.8rem' }}>
              {incident.intent && (
                <div>
                  <span style={{ color: 'var(--text-dim)' }}>Intent / Causality:</span>
                  <div style={{ fontWeight: 600, color: incident.intent === 'intentional_misuse' ? '#f87171' : '#a7f3d0' }}>
                    {incident.intent.replace(/_/g, ' ')}
                  </div>
                </div>
              )}
              {incident.primary_purpose && (
                <div>
                  <span style={{ color: 'var(--text-dim)' }}>Primary AI Purpose:</span>
                  <div style={{ fontWeight: 600 }}>{incident.primary_purpose.replace(/_/g, ' ')}</div>
                </div>
              )}
              {incident.harm_type && (
                <div>
                  <span style={{ color: 'var(--text-dim)' }}>CSET Harm Type:</span>
                  <div style={{ fontWeight: 600, color: 'var(--accent-purple)' }}>{incident.harm_type.replace(/_/g, ' ')}</div>
                </div>
              )}
              {incident.eu_ai_act_tier && (
                <div>
                  <span style={{ color: 'var(--text-dim)' }}>EU AI Act Tier:</span>
                  <div style={{ fontWeight: 600, color: '#93c5fd' }}>{incident.eu_ai_act_tier.replace(/_/g, ' ')}</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Taxonomy Metadata Grid */}
        <div className="detail-section">
          <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <ShieldCheck size={14} /> Taxonomy Classification & Confidence Scores
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.8rem' }}>
            <div>
              <span style={{ color: 'var(--text-dim)' }}>Lifecycle Phase:</span>
              <div style={{ fontWeight: 600 }}>{incident.lifecycle_phase.replace(/_/g, ' ')}</div>
              <span className="confidence-tag">
                {Math.round((incident.confidence_scores?.lifecycle_phase ?? 1.0) * 100)}% Conf.
              </span>
            </div>
            <div>
              <span style={{ color: 'var(--text-dim)' }}>System Classification:</span>
              <div style={{ fontWeight: 600 }}>{incident.system_classification.replace(/_/g, ' ')}</div>
              <span className="confidence-tag">
                {Math.round((incident.confidence_scores?.system_classification ?? 1.0) * 100)}% Conf.
              </span>
            </div>
            <div>
              <span style={{ color: 'var(--text-dim)' }}>Root Cause (MIT):</span>
              <div style={{ fontWeight: 600 }}>
                {incident.root_cause_category} {incident.root_cause_subtype ? `(${incident.root_cause_subtype})` : ''}
              </div>
              <span className="confidence-tag">
                {Math.round((incident.confidence_scores?.root_cause_category ?? 1.0) * 100)}% Conf.
              </span>
            </div>
            <div>
              <span style={{ color: 'var(--text-dim)' }}>Harm Domain (OECD):</span>
              <div style={{ fontWeight: 600 }}>{incident.harm_domain.replace(/_/g, ' ')}</div>
              <span className="confidence-tag">
                {Math.round((incident.confidence_scores?.harm_domain ?? 1.0) * 100)}% Conf.
              </span>
            </div>
          </div>
        </div>

        {/* Linked Knowledge Graph Connections */}
        {connectedEdges.length > 0 && (
          <div className="detail-section">
            <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <GitFork size={14} /> Knowledge Graph Timeline Links ({connectedEdges.length})
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {connectedEdges.map((edge) => {
                const otherId = edge.source_id === incident.incident_id ? edge.target_id : edge.source_id;
                const otherIncident = incidentMap.get(otherId);

                return (
                  <div
                    key={edge.edge_id}
                    onClick={() => otherIncident && onSelectRelated(otherIncident)}
                    style={{
                      padding: '0.5rem',
                      background: 'rgba(255,255,255,0.03)',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.8rem',
                      border: '1px dashed var(--border-color)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--accent-cyan)' }}>
                      <span style={{ fontWeight: 600 }}>{edge.relation_type.replace(/_/g, ' ')}</span>
                      <span>{otherId}</span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {edge.description}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Source URLs */}
        <div className="detail-section">
          <h4>Source Evidence URLs</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.8rem' }}>
            {incident.source_urls.map((url, idx) => (
              <a
                key={idx}
                href={url}
                target="_blank"
                rel="noreferrer"
                style={{ color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', gap: '0.3rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
              >
                <ExternalLink size={12} /> {url}
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
