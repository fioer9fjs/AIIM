import React, { useEffect, useRef, useState, useMemo } from 'react';
import { AIIncident, GraphEdge } from '../types/incident';
import { Filter, Search, RotateCcw, Layers, Play, Pause, Maximize2 } from 'lucide-react';
// Import vis-network and vis-data
import { Network, Options, Node, Edge, DataSet } from 'vis-network/standalone';

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
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);

  const [clusterCategory, setClusterCategory] = useState<string>('none');
  const [relationFilter, setRelationFilter] = useState<string>('all');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [physicsEnabled, setPhysicsEnabled] = useState<boolean>(true);

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

  // Filter edges based on relationFilter
  const filteredEdges = useMemo(() => {
    const validIds = new Set(filteredIncidents.map((i) => i.incident_id));
    return edges.filter(
      (e) => validIds.has(e.source_id) && validIds.has(e.target_id) && (relationFilter === 'all' || e.relation_type === relationFilter)
    );
  }, [edges, filteredIncidents, relationFilter]);

  // Initialize and update Vis-Network Canvas
  useEffect(() => {
    if (!containerRef.current) return;

    // Build Vis Nodes
    const visNodes: Node[] = filteredIncidents.map((inc) => {
      const color = SEVERITY_COLORS[inc.severity] || '#3b82f6';
      const incAny = inc as any;
      return {
        id: inc.incident_id,
        label: inc.title.length > 28 ? `${inc.title.substring(0, 25)}...` : inc.title,
        title: `<b>${inc.incident_id}</b><br/>${inc.title}<br/><i>Severity: ${inc.severity.toUpperCase()}</i>`,
        shape: 'dot',
        size: inc.severity === 'critical' ? 22 : inc.severity === 'high' ? 18 : 14,
        color: {
          background: color,
          border: '#ffffff',
          highlight: { background: '#38bdf8', border: '#ffffff' },
          hover: { background: '#38bdf8', border: '#ffffff' }
        },
        font: { color: '#f8fafc', face: 'Inter', size: 12, strokeWidth: 3, strokeColor: '#0f172a' },
        shadow: { enabled: true, color: 'rgba(0,0,0,0.6)', size: 10, x: 2, y: 4 },
        // Custom properties for clustering
        eu_risk_tier: incAny.eu_risk_tier || 'unclassified',
        harm_domain: incAny.harm_domain || 'undetermined',
        primary_purpose: incAny.primary_purpose || 'other',
        system_classification: incAny.system_classification || 'unclassified',
        severity: inc.severity || 'medium'
      };
    });

    // Build Vis Edges
    const visEdges: Edge[] = filteredEdges.map((e) => ({
      id: e.edge_id,
      from: e.source_id,
      to: e.target_id,
      label: e.relation_type.replace(/_/g, ' '),
      arrows: { to: { enabled: true, scaleFactor: 0.8 } },
      color: { color: '#3b82f6', opacity: 0.7, highlight: '#38bdf8' },
      dashes: e.relation_type === 'lawsuit' || e.relation_type === 'regulatory_action',
      font: { color: '#94a3b8', size: 10, align: 'middle', background: 'rgba(15, 23, 42, 0.8)' },
      width: 2
    }));

    const nodesDataSet = new DataSet(visNodes);
    const edgesDataSet = new DataSet(visEdges);

    const options: Options = {
      nodes: {
        borderWidth: 2
      },
      edges: {
        smooth: {
          type: 'continuous',
          roundness: 0.2
        }
      },
      physics: {
        enabled: physicsEnabled,
        barnesHut: {
          gravitationalConstant: -14000,
          centralGravity: 0.05,
          springLength: 220,
          springConstant: 0.02,
          damping: 0.09,
          avoidOverlap: 0.8
        },
        stabilization: {
          iterations: 200
        }
      },
      interaction: {
        dragNodes: true,
        dragView: true,
        zoomView: true,
        hover: true,
        tooltipDelay: 100
      }
    };

    const network = new Network(containerRef.current, { nodes: nodesDataSet, edges: edgesDataSet }, options);
    networkRef.current = network;

    // Auto-fit after stabilization
    network.on('stabilizationIterationsDone', () => {
      network.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
    });

    // Node click handler with explicit params type
    network.on('click', (params: { nodes?: (string | number)[] }) => {
      if (params.nodes && params.nodes.length > 0) {
        const nodeId = String(params.nodes[0]);
        // Check if clicked item is a cluster
        if (network.isCluster(nodeId)) {
          network.openCluster(nodeId);
          return;
        }
        const targetInc = incidents.find((i) => i.incident_id === nodeId);
        if (targetInc) {
          onSelectIncident(targetInc);
        }
      }
    });

    return () => {
      network.destroy();
      networkRef.current = null;
    };
  }, [filteredIncidents, filteredEdges, physicsEnabled, incidents, onSelectIncident]);

  // Apply Categorical Clustering when clusterCategory changes
  useEffect(() => {
    const network = networkRef.current;
    if (!network) return;

    // First open all existing clusters
    const clusterIds = Object.keys(network.body.nodes).filter((id) => network.isCluster(id));
    clusterIds.forEach((cId) => network.openCluster(cId));

    if (clusterCategory === 'none') return;

    const propertyMap: Record<string, string> = {
      eu_risk_tier: 'EU Risk Tier',
      harm_domain: 'Harm Domain',
      primary_purpose: 'Primary Purpose',
      system_classification: 'System Type',
      severity: 'Severity Level'
    };

    const clusterKey = clusterCategory;
    const propertyLabel = propertyMap[clusterKey] || 'Cluster';

    const uniqueValues = new Set<string>();
    filteredIncidents.forEach((inc) => {
      const val = (inc as any)[clusterKey] || 'Unclassified';
      uniqueValues.add(val);
    });

    uniqueValues.forEach((val) => {
      const clusterOptions = {
        joinCondition: (childOptions: any) => {
          return childOptions[clusterKey] === val;
        },
        processProperties: (clusterOptions: any, childNodes: any[]) => {
          const count = childNodes.length;
          let labelText = `${propertyLabel}:\n${val.replace(/_/g, ' ').toUpperCase()} (${count})`;
          return {
            title: `<b>${propertyLabel}: ${val}</b><br/>Contains ${count} incidents. Click to expand.`,
            label: labelText,
            color: {
              background: '#1e293b',
              border: '#38bdf8',
              highlight: { background: '#0284c7', border: '#ffffff' }
            },
            shape: 'hexagon',
            size: 25 + Math.min(count * 3, 25),
            font: { color: '#f8fafc', size: 11, face: 'Inter', multi: 'html' }
          };
        },
        clusterNodeProperties: {
          id: `cluster_${clusterKey}_${val}`,
          borderWidth: 3
        }
      };
      network.cluster(clusterOptions);
    });
  }, [clusterCategory, filteredIncidents]);

  const handleResetFilters = () => {
    setClusterCategory('none');
    setRelationFilter('all');
    setSeverityFilter('all');
    setSearchQuery('');
    if (networkRef.current) {
      networkRef.current.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
    }
  };

  const handleFitView = () => {
    if (networkRef.current) {
      networkRef.current.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
    }
  };

  const togglePhysics = () => {
    setPhysicsEnabled((prev) => !prev);
  };

  return (
    <div className="graph-viewport" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 160px)', minHeight: '680px', width: '100%' }}>
      {/* Controls Bar */}
      <div
        style={{
          padding: '1rem 1.5rem',
          background: 'rgba(15, 23, 42, 0.95)',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '1rem',
          justifyContent: 'space-between',
          alignItems: 'center',
          backdropFilter: 'blur(10px)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Filter size={20} style={{ color: 'var(--accent-cyan)' }} />
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
              Interactive Causal Knowledge Graph
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Showing {filteredIncidents.length} Nodes & {filteredEdges.length} Causal Edges • Drag nodes freely or click to inspect
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.65rem', flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Node Search */}
          <div className="search-input-wrapper" style={{ width: '170px' }}>
            <Search className="search-icon" size={13} />
            <input
              type="text"
              className="search-input"
              style={{ padding: '0.35rem 0.5rem 0.35rem 2rem', fontSize: '0.8rem' }}
              placeholder="Search node title..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Dynamic Category Clustering Dropdown */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <Layers size={14} style={{ color: 'var(--accent-cyan)' }} />
            <select
              className="filter-select"
              style={{ width: '175px', padding: '0.35rem 0.5rem', fontSize: '0.8rem', borderColor: 'var(--accent-cyan)' }}
              value={clusterCategory}
              onChange={(e) => setClusterCategory(e.target.value)}
            >
              <option value="none">🌐 No Clustering (Flat)</option>
              <option value="eu_risk_tier">🏛️ Cluster by EU AI Act Tier</option>
              <option value="harm_domain">⚠️ Cluster by Harm Domain</option>
              <option value="primary_purpose">🎯 Cluster by Primary Purpose</option>
              <option value="system_classification">🤖 Cluster by System Type</option>
              <option value="severity">🔥 Cluster by Severity</option>
            </select>
          </div>

          {/* Relation Type Filter */}
          <select
            className="filter-select"
            style={{ width: '145px', padding: '0.35rem 0.5rem', fontSize: '0.8rem' }}
            value={relationFilter}
            onChange={(e) => setRelationFilter(e.target.value)}
          >
            <option value="all">All Edge Types</option>
            <option value="lawsuit">Lawsuit / Litigation</option>
            <option value="regulatory_action">Regulatory Action</option>
            <option value="patch">Patch / Fix</option>
            <option value="related_cause">Related Cause</option>
          </select>

          {/* Severity Filter */}
          <select
            className="filter-select"
            style={{ width: '130px', padding: '0.35rem 0.5rem', fontSize: '0.8rem' }}
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          {/* Physics Toggle Button */}
          <button
            onClick={togglePhysics}
            className="button button-outline"
            style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
            title={physicsEnabled ? 'Freeze Physics Simulation' : 'Enable Physics Simulation'}
          >
            {physicsEnabled ? <Pause size={13} style={{ color: '#ef4444' }} /> : <Play size={13} style={{ color: '#10b981' }} />}
            {physicsEnabled ? 'Pause Physics' : 'Live Physics'}
          </button>

          {/* Fit View Button */}
          <button
            onClick={handleFitView}
            className="button button-outline"
            style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
            title="Recenter & Fit View"
          >
            <Maximize2 size={13} /> Fit
          </button>

          {/* Reset button */}
          <button
            onClick={handleResetFilters}
            className="button button-outline"
            style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
          >
            <RotateCcw size={12} /> Reset
          </button>
        </div>
      </div>

      {/* Main Vis-Network Canvas Container */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden', background: '#070a12', width: '100%' }}>
        <div ref={containerRef} style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, width: '100%', height: '100%' }} />

        {/* Legend */}
        <div
          style={{
            position: 'absolute',
            bottom: '1rem',
            left: '1rem',
            background: 'rgba(15, 23, 42, 0.9)',
            border: '1px solid var(--border-color)',
            padding: '0.75rem 1rem',
            borderRadius: '8px',
            display: 'flex',
            gap: '1.25rem',
            fontSize: '0.75rem',
            backdropFilter: 'blur(8px)',
            pointerEvents: 'none'
          }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#cbd5e1' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444' }} /> Critical
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#cbd5e1' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#f97316' }} /> High
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#cbd5e1' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#eab308' }} /> Medium
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#cbd5e1' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#3b82f6' }} /> Low
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#cbd5e1', borderLeft: '1px solid #334155', paddingLeft: '1rem' }}>
            <span style={{ width: 12, height: 12, background: '#1e293b', border: '2px solid #38bdf8' }} /> Category Cluster (Click to open)
          </span>
        </div>
      </div>
    </div>
  );
};
