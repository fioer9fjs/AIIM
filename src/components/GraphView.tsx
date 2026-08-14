import React, { useState, useMemo } from 'react';
import { AIIncident, GraphEdge } from '../types/incident';
import { Filter, Search, RotateCcw } from 'lucide-react';

interface GraphViewProps {
  incidents: AIIncident[];
  edges: GraphEdge[];
  onSelectIncident: (incident: AIIncident) => void;
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6'
};

export const GraphView: React.FC<GraphViewProps> = ({ incidents, edges, onSelectIncident }) => {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [relationFilter, setRelationFilter] = useState<string>('all');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Filter edges based on relationFilter
  const filteredEdges = useMemo(() => {
    return edges.filter((e) => relationFilter === 'all' || e.relation_type === relationFilter);
  }, [edges, relationFilter]);

  // Filter incidents based on severity and search
  const filteredIncidents = useMemo(() => {
    return incidents.filter((inc) => {
      const matchesSeverity = severityFilter === 'all' || inc.severity === severityFilter;
      const matchesSearch =
        searchQuery === '' ||
        inc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        inc.incident_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (inc.affected_parties && inc.affected_parties.some((p) => p.toLowerCase().includes(searchQuery.toLowerCase())));

      return matchesSeverity && matchesSearch;
    });
  }, [incidents, severityFilter, searchQuery]);

  const nodesWithPos = useMemo(() => {
    return filteredIncidents.map((inc, index) => {
      const angle = (index / (filteredIncidents.length || 1)) * 2 * Math.PI;
      const radius = 220 + (index % 2) * 60;
      const cx = 450 + radius * Math.cos(angle);
      const cy = 300 + radius * Math.sin(angle);
      return { ...inc, x: cx, y: cy };
    });
  }, [filteredIncidents]);

  const nodeMap = useMemo(() => new Map(nodesWithPos.map((n) => [n.incident_id, n])), [nodesWithPos]);

  // Find connected incident IDs for selected node
  const connectedNodeIds = useMemo(() => {
    if (!selectedNodeId) return new Set<string>();
    const set = new Set<string>([selectedNodeId]);
    filteredEdges.forEach((e) => {
      if (e.source_id === selectedNodeId) set.add(e.target_id);
      if (e.target_id === selectedNodeId) set.add(e.source_id);
    });
    return set;
  }, [selectedNodeId, filteredEdges]);

  const handleResetGraphFilters = () => {
    setRelationFilter('all');
    setSeverityFilter('all');
    setSearchQuery('');
    setSelectedNodeId(null);
  };

  return (
    <div className="graph-viewport" style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '650px' }}>
      {/* Controls Bar */}
      <div
        style={{
          padding: '1rem 1.5rem',
          background: 'rgba(0,0,0,0.5)',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '1rem',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Filter size={18} style={{ color: 'var(--accent-cyan)' }} />
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)' }}>Knowledge Graph Filters</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Showing {nodesWithPos.length} Nodes & {filteredEdges.length} Causal Edges
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Node Search */}
          <div className="search-input-wrapper" style={{ width: '180px' }}>
            <Search className="search-icon" size={13} />
            <input
              type="text"
              className="search-input"
              style={{ padding: '0.35rem 0.5rem 0.35rem 2rem', fontSize: '0.8rem' }}
              placeholder="Search node..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Relation Type Filter */}
          <select
            className="filter-select"
            style={{ width: '150px', padding: '0.35rem 0.5rem', fontSize: '0.8rem' }}
            value={relationFilter}
            onChange={(e) => setRelationFilter(e.target.value)}
          >
            <option value="all">All Relation Edges</option>
            <option value="lawsuit">Lawsuit / Litigation</option>
            <option value="regulatory_action">Regulatory Action</option>
            <option value="patch">Patch / Fix</option>
            <option value="related_cause">Related Cause</option>
          </select>

          {/* Severity Filter */}
          <select
            className="filter-select"
            style={{ width: '140px', padding: '0.35rem 0.5rem', fontSize: '0.8rem' }}
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          {/* Reset button */}
          <button
            onClick={handleResetGraphFilters}
            className="button button-outline"
            style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
          >
            <RotateCcw size={12} /> Reset
          </button>
        </div>
      </div>

      {/* Main SVG Graph Canvas */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden', background: '#090d16' }}>
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

          {/* Edges */}
          {filteredEdges.map((edge) => {
            const source = nodeMap.get(edge.source_id);
            const target = nodeMap.get(edge.target_id);

            if (!source || !target) return null;

            const isHighlighted =
              selectedNodeId === null || (connectedNodeIds.has(source.incident_id) && connectedNodeIds.has(target.incident_id));

            return (
              <g key={edge.edge_id} opacity={isHighlighted ? 0.9 : 0.15}>
                <line
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                  stroke={isHighlighted ? '#3b82f6' : '#334155'}
                  strokeWidth={isHighlighted ? '2.5' : '1'}
                  strokeDasharray={edge.relation_type === 'lawsuit' ? '4,4' : undefined}
                  markerEnd="url(#arrow)"
                />
                <text
                  x={(source.x + target.x) / 2}
                  y={(source.y + target.y) / 2 - 8}
                  fill={isHighlighted ? '#94a3b8' : '#475569'}
                  fontSize="10"
                  textAnchor="middle"
                  fontFamily="Inter"
                >
                  {edge.relation_type.replace(/_/g, ' ')}
                </text>
              </g>
            );
          })}

          {/* Nodes */}
          {nodesWithPos.map((node) => {
            const isSelected = selectedNodeId === node.incident_id;
            const isConnected = connectedNodeIds.has(node.incident_id);
            const nodeOpacity = selectedNodeId === null || isConnected ? 1 : 0.25;

            return (
              <g
                key={node.incident_id}
                transform={`translate(${node.x},${node.y})`}
                style={{ cursor: 'pointer', transition: 'all 0.2s ease' }}
                opacity={nodeOpacity}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedNodeId(node.incident_id);
                  onSelectIncident(node);
                }}
              >
                <circle
                  r={isSelected ? 16 : 12}
                  fill={SEVERITY_COLORS[node.severity] || '#3b82f6'}
                  stroke={isSelected ? '#ffffff' : 'rgba(255,255,255,0.4)'}
                  strokeWidth={isSelected ? 3 : 1.5}
                />
                <text
                  y={24}
                  fill="#f8fafc"
                  fontSize="11"
                  fontWeight={isSelected ? 700 : 500}
                  textAnchor="middle"
                  fontFamily="Inter"
                >
                  {node.title.length > 25 ? `${node.title.substring(0, 22)}...` : node.title}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Legend */}
        <div
          style={{
            position: 'absolute',
            bottom: '1rem',
            left: '1rem',
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid var(--border-color)',
            padding: '0.75rem 1rem',
            borderRadius: '8px',
            display: 'flex',
            gap: '1rem',
            fontSize: '0.75rem',
            backdropFilter: 'blur(8px)'
          }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444' }} /> Critical
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#f97316' }} /> High
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#eab308' }} /> Medium
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#3b82f6' }} /> Low
          </span>
        </div>
      </div>
    </div>
  );
};
