import React, { useState, useMemo } from 'react';
import { AIIncident, formatFinancialDamage } from '../types/incident';
import { Globe, ShieldAlert, DollarSign, MapPin } from 'lucide-react';

interface GeoMapViewProps {
  incidents: AIIncident[];
  onSelectIncident: (incident: AIIncident) => void;
}

// Country & Region Centroid Coordinate Coordinates (Mapped to SVG 900x500 canvas)
const REGION_COORDINATES: Record<string, { name: string; cx: number; cy: number }> = {
  'united states': { name: 'United States', cx: 210, cy: 190 },
  'usa': { name: 'United States', cx: 210, cy: 190 },
  'us': { name: 'United States', cx: 210, cy: 190 },
  'canada': { name: 'Canada', cx: 200, cy: 120 },
  'united kingdom': { name: 'United Kingdom', cx: 435, cy: 140 },
  'uk': { name: 'United Kingdom', cx: 435, cy: 140 },
  'european union': { name: 'European Union', cx: 470, cy: 160 },
  'eu': { name: 'European Union', cx: 470, cy: 160 },
  'germany': { name: 'Germany', cx: 465, cy: 155 },
  'france': { name: 'France', cx: 445, cy: 165 },
  'china': { name: 'China', cx: 680, cy: 200 },
  'japan': { name: 'Japan', cx: 760, cy: 200 },
  'india': { name: 'India', cx: 630, cy: 245 },
  'australia': { name: 'Australia', cx: 750, cy: 370 },
  'brazil': { name: 'Brazil', cx: 310, cy: 320 },
  'global': { name: 'Global / Multi-Region', cx: 450, cy: 260 }
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6'
};

export const GeoMapView: React.FC<GeoMapViewProps> = ({ incidents, onSelectIncident }) => {
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);

  // Group incidents by geographic scope region
  const regionMap = useMemo(() => {
    const map = new Map<string, AIIncident[]>();
    incidents.forEach((inc) => {
      const scopes = inc.geographic_scope && inc.geographic_scope.length > 0 ? inc.geographic_scope : ['Global'];
      scopes.forEach((scope) => {
        const key = scope.toLowerCase().strip ? scope.toLowerCase().trim() : scope.toLowerCase();
        if (!map.has(key)) map.set(key, []);
        map.get(key)!.push(inc);
      });
    });
    return map;
  }, [incidents]);

  const activeIncidents = useMemo(() => {
    if (!selectedCountry) return incidents;
    return regionMap.get(selectedCountry.toLowerCase()) || [];
  }, [selectedCountry, regionMap, incidents]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header bar */}
      <div className="detail-section" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Globe size={20} style={{ color: 'var(--accent-cyan)' }} /> Global AI Incident Distribution Map
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Interactive geospatial overview of AI safety events, regulatory enforcement, and financial damage across countries.
          </p>
        </div>

        {selectedCountry && (
          <button
            onClick={() => setSelectedCountry(null)}
            className="button button-outline"
            style={{ fontSize: '0.8rem' }}
          >
            Show All Countries ({incidents.length} incidents)
          </button>
        )}
      </div>

      {/* World Map SVG Vector Viewport */}
      <div
        className="detail-section"
        style={{
          position: 'relative',
          padding: '1rem',
          background: '#090d16',
          borderRadius: '12px',
          overflow: 'hidden'
        }}
      >
        <svg viewBox="0 0 900 480" width="100%" height="100%" style={{ background: '#070a12', borderRadius: '8px' }}>
          {/* World Grid Lines */}
          <line x1="0" y1="240" x2="900" y2="240" stroke="#1e293b" strokeDasharray="3,3" />
          <line x1="450" y1="0" x2="450" y2="480" stroke="#1e293b" strokeDasharray="3,3" />

          {/* Continents Vector Outlines */}
          {/* North America */}
          <path d="M 120 100 L 260 80 L 290 140 L 250 240 L 190 260 L 150 200 Z" fill="#1e293b" opacity="0.4" stroke="#334155" />
          {/* South America */}
          <path d="M 270 270 L 340 280 L 330 400 L 280 430 L 260 340 Z" fill="#1e293b" opacity="0.4" stroke="#334155" />
          {/* Europe */}
          <path d="M 420 110 L 510 100 L 520 180 L 430 190 Z" fill="#1e293b" opacity="0.4" stroke="#334155" />
          {/* Africa */}
          <path d="M 420 200 L 520 200 L 530 330 L 470 370 L 420 270 Z" fill="#1e293b" opacity="0.4" stroke="#334155" />
          {/* Asia */}
          <path d="M 530 90 L 780 90 L 800 240 L 620 260 L 530 180 Z" fill="#1e293b" opacity="0.4" stroke="#334155" />
          {/* Australia */}
          <path d="M 700 320 L 790 320 L 780 400 L 710 400 Z" fill="#1e293b" opacity="0.4" stroke="#334155" />

          {/* Incident Region Pulse Markers */}
          {Object.entries(REGION_COORDINATES).map(([key, reg]) => {
            const regionIncidents = regionMap.get(key) || [];
            if (regionIncidents.length === 0) return null;

            const isSelected = selectedCountry?.toLowerCase() === key;
            const criticalCount = regionIncidents.filter((i) => i.severity === 'critical').length;
            const markerColor = criticalCount > 0 ? '#ef4444' : '#38bdf8';

            return (
              <g
                key={key}
                transform={`translate(${reg.cx},${reg.cy})`}
                style={{ cursor: 'pointer' }}
                onClick={() => setSelectedCountry(isSelected ? null : key)}
              >
                {/* Pulsing ring */}
                <circle r={14 + regionIncidents.length * 2} fill={markerColor} opacity="0.2" className="pulse-ring">
                  <animate attributeName="r" values="10;22;10" dur="3s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.4;0.1;0.4" dur="3s" repeatCount="indefinite" />
                </circle>

                <circle r={10 + Math.min(regionIncidents.length, 6)} fill={markerColor} stroke="#ffffff" strokeWidth={isSelected ? 2.5 : 1.5} />

                <text y={4} fill="#ffffff" fontSize="10" fontWeight="700" textAnchor="middle">
                  {regionIncidents.length}
                </text>

                <text y={24} fill="#94a3b8" fontSize="10" fontWeight="600" textAnchor="middle">
                  {reg.name}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Floating Controls Overlay */}
        <div style={{ position: 'absolute', bottom: '1.5rem', right: '1.5rem', background: 'rgba(15, 23, 42, 0.85)', padding: '0.5rem 1rem', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.75rem' }}>
          <span>Click any country marker to isolate incidents</span>
        </div>
      </div>

      {/* Country Incident List */}
      <div className="detail-section">
        <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <MapPin size={16} style={{ color: 'var(--accent-cyan)' }} />
          Incidents for Region: <span style={{ color: 'var(--accent-purple)' }}>{selectedCountry ? REGION_COORDINATES[selectedCountry.toLowerCase()]?.name || selectedCountry : 'All Global Regions'}</span>
          <span className="badge" style={{ backgroundColor: 'rgba(56, 189, 248, 0.2)', color: 'var(--accent-cyan)' }}>{activeIncidents.length} Total</span>
        </h3>

        <div className="grid-cards">
          {activeIncidents.map((inc) => (
            <div key={inc.incident_id} className="incident-card" onClick={() => onSelectIncident(inc)}>
              <div className="card-header">
                <span className={`badge badge-${inc.severity}`}>{inc.severity}</span>
                <span className={`badge badge-${inc.verification_status}`}>{inc.verification_status}</span>
                <span className="badge" style={{ backgroundColor: 'rgba(168, 85, 247, 0.2)', color: '#d8b4fe' }}>
                  Src: {(inc.source_type || 'google_news_rss').replace(/_/g, ' ')}
                </span>
                {inc.financial_damage_usd ? inc.financial_damage_usd > 0 ? (
                  <span className="badge" style={{ backgroundColor: 'rgba(16, 185, 129, 0.2)', color: '#34d399', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                    <DollarSign size={12} /> {formatFinancialDamage(inc.financial_damage_usd)}
                  </span>
                ) : null : null}
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
                </div>
                <span className="details-link">Details →</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
