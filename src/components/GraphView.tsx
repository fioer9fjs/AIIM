import React, { useState } from 'react';
import { AIIncident, GraphEdge } from '../types/incident';

interface GraphViewProps {
  incidents: AIIncident[];
  edges: GraphEdge[];
  onSelectIncident: (incident: AIIncident) => void;
}

export const GraphView: React.FC<GraphViewProps> = ({ incidents, edges, onSelectIncident }) => {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const nodesWithPos = incidents.map((inc, index) => {
    const angle = (index / (incidents.length || 1)) * 2 * Math.PI;
    const radius = 220 + (index % 2) * 60;
    const cx = 450 + radius * Math.cos(angle);
    const cy = 300 + radius * Math.sin(angle);
    return { ...inc, x: cx, y: cy };
  });

  const nodeMap = new Map(nodesWithPos.map((n) => [n.incident_id, n]));

  return (
    <div className="graph-viewport" style={{ display: 'flex', flexDirection: 'column' }}>
      <div
        style={{
          padding: '1rem 1.5rem',
          background: 'rgba(0,0,0,0.4)',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Interactive Knowledge Graph</h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Nodes represent AI Incidents - Edges connect causal developments, patches, and legal follow-ups
          </p>
        </div>
        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444' }} /> Critical
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#f97316' }} /> High
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#3b82f6' }} /> Low/Patch
          </span>
        </div>
      </div>

      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        <svg width="100%" height="100%" viewBox="0 0 900 600">
          <defs>
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="18"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#3b82f6" />
            </marker>
          </defs>

          {edges.map((edge) => {
            const source = nodeMap.get(edge.source_id);
            const target = nodeMap.get(edge.target_id);

            if (!source || !target) return null;

            return (
              <g key={edge.edge_id}>
                <line
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                  stroke="#3b82f6"
                  strokeWidth="2"
                  strokeDasharray={edge.relation_type === 'lawsuit' ? '4,4' : undefined}
                  markerEnd="url(#arrow)"
                  opacity="0.8"
                />
                <text
                  x={(source.x + target.x) / 2}
                  y={(source.y + target.y) / 2 - 8}
                  fill="#94a3b8"
                  fontSize="10"
                  textAnchor="middle"
                  fontFamily="Inter"
                >
                  {edge.relation_type.replace(/_/g, ' ')}
                </text>
              </g>
            );
          })}

          {nodesWithPos.map((node) => {
            const isSelected = selectedNodeId === node.incident_id;
            let nodeColor = '#3b82f6';
            if (node.severity === 'critical') nodeColor = '#ef4444';
            else if (node.severity === 'high') nodeColor = '#f97316';
            else if (node.severity === 'medium') nodeColor = '#eab308';

            return (
              <g
                key={node.incident_id}
                transform={`translate(${node.x}, ${node.y})`}
                style={{ cursor: 'pointer' }}
                onClick={() => {
                  setSelectedNodeId(node.incident_id);
                  onSelectIncident(node);
                }}
              >
                <circle
                  r={isSelected ? 18 : 14}
                  fill={nodeColor}
                  stroke={isSelected ? '#ffffff' : 'rgba(255,255,255,0.3)'}
                  strokeWidth={isSelected ? 3 : 1.5}
                />
                <text
                  y="26"
                  fill="#f8fafc"
                  fontSize="11"
                  fontWeight="600"
                  textAnchor="middle"
                  fontFamily="Inter"
                >
                  {node.incident_id}
                </text>
                <text
                  y="38"
                  fill="#94a3b8"
                  fontSize="9"
                  textAnchor="middle"
                  fontFamily="Inter"
                >
                  {node.affected_parties[0] || node.title.slice(0, 20)}...
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};
