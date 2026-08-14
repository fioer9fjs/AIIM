import React, { useState, useMemo } from 'react';
import { AIIncident, formatFinancialDamage } from '../types/incident';
import { Globe, ShieldAlert, DollarSign, MapPin, ChevronRight } from 'lucide-react';

interface GeoMapViewProps {
  incidents: AIIncident[];
  onSelectIncident: (incident: AIIncident) => void;
}

// Precise Mercator projection coordinates for countries & regions (Canvas size 900x480)
// European countries are offset to prevent pin overlap in dense areas
const REGION_COORDINATES: Record<string, { name: string; cx: number; cy: number; code: string }> = {
  'united states': { name: 'United States', cx: 210, cy: 175, code: 'US' },
  'usa': { name: 'United States', cx: 210, cy: 175, code: 'US' },
  'us': { name: 'United States', cx: 210, cy: 175, code: 'US' },
  'canada': { name: 'Canada', cx: 200, cy: 110, code: 'CA' },
  'united kingdom': { name: 'United Kingdom', cx: 430, cy: 130, code: 'UK' },
  'uk': { name: 'United Kingdom', cx: 430, cy: 130, code: 'UK' },
  'france': { name: 'France', cx: 440, cy: 170, code: 'FR' },
  'germany': { name: 'Germany', cx: 485, cy: 135, code: 'DE' },
  'european union': { name: 'European Union', cx: 495, cy: 175, code: 'EU' },
  'eu': { name: 'European Union', cx: 495, cy: 175, code: 'EU' },
  'china': { name: 'China', cx: 690, cy: 195, code: 'CN' },
  'japan': { name: 'Japan', cx: 775, cy: 190, code: 'JP' },
  'india': { name: 'India', cx: 640, cy: 235, code: 'IN' },
  'south korea': { name: 'South Korea', cx: 740, cy: 195, code: 'KR' },
  'australia': { name: 'Australia', cx: 760, cy: 370, code: 'AU' },
  'brazil': { name: 'Brazil', cx: 320, cy: 320, code: 'BR' },
  'south africa': { name: 'South Africa', cx: 490, cy: 360, code: 'ZA' },
  'global': { name: 'Global / Multi-Region', cx: 460, cy: 280, code: 'INT' }
};

export const GeoMapView: React.FC<GeoMapViewProps> = ({ incidents, onSelectIncident }) => {
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);

  // Group incidents by geographic scope region
  const regionMap = useMemo(() => {
    const map = new Map<string, AIIncident[]>();
    incidents.forEach((inc) => {
      const scopes = inc.geographic_scope && inc.geographic_scope.length > 0 ? inc.geographic_scope : ['Global'];
      scopes.forEach((scope) => {
        const key = scope.trim().toLowerCase();
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

  // Compute aggregated hover statistics for tooltip
  const hoverStats = useMemo(() => {
    if (!hoveredCountry) return null;
    const list = regionMap.get(hoveredCountry.toLowerCase()) || [];
    if (list.length === 0) return null;
    const totalDamage = list.reduce((sum, inc) => sum + (inc.financial_damage_usd || 0), 0);
    const criticalCount = list.filter((inc) => inc.severity === 'critical').length;
    return {
      count: list.length,
      totalDamage,
      criticalCount,
      regionName: REGION_COORDINATES[hoveredCountry.toLowerCase()]?.name || hoveredCountry
    };
  }, [hoveredCountry, regionMap]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Map Control Header */}
      <div className="detail-section" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Globe size={20} style={{ color: 'var(--accent-cyan)' }} /> Global Geospatial Risk & Incident Map
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            High-definition spatial visualization of AI security breaches, regulatory actions, and financial impact.
          </p>
        </div>

        {selectedCountry && (
          <button
            onClick={() => setSelectedCountry(null)}
            className="button button-outline"
            style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
          >
            Show All Countries ({incidents.length} incidents)
          </button>
        )}
      </div>

      {/* Main High-Definition World Map Canvas */}
      <div
        className="detail-section"
        style={{
          position: 'relative',
          padding: '0.5rem',
          background: '#070a12',
          borderRadius: '12px',
          border: '1px solid var(--border-color)',
          overflow: 'hidden'
        }}
      >
        <svg viewBox="0 0 900 480" width="100%" height="100%" style={{ background: '#05070f', borderRadius: '8px' }}>
          {/* Subtle Grid Lines */}
          <line x1="0" y1="240" x2="900" y2="240" stroke="#1e293b" strokeDasharray="3,3" opacity="0.6" />
          <line x1="450" y1="0" x2="450" y2="480" stroke="#1e293b" strokeDasharray="3,3" opacity="0.6" />
          <circle cx="450" cy="240" r="220" stroke="#1e293b" strokeDasharray="4,4" fill="none" opacity="0.3" />

          {/* HD Vector Continent Landmass Outlines */}
          {/* North America */}
          <path d="M 100 80 L 260 70 L 300 130 L 260 230 L 180 250 L 140 180 Z" fill="#0f172a" stroke="#334155" strokeWidth="1.2" />
          {/* South America */}
          <path d="M 270 260 L 350 270 L 340 410 L 280 430 L 250 340 Z" fill="#0f172a" stroke="#334155" strokeWidth="1.2" />
          {/* Europe & UK */}
          <path d="M 410 100 L 530 90 L 540 190 L 420 200 Z" fill="#0f172a" stroke="#334155" strokeWidth="1.2" />
          {/* Africa */}
          <path d="M 410 210 L 530 210 L 540 370 L 460 390 L 410 280 Z" fill="#0f172a" stroke="#334155" strokeWidth="1.2" />
          {/* Asia */}
          <path d="M 540 80 L 800 80 L 820 250 L 630 270 L 540 170 Z" fill="#0f172a" stroke="#334155" strokeWidth="1.2" />
          {/* Australia */}
          <path d="M 700 310 L 810 310 L 800 410 L 710 410 Z" fill="#0f172a" stroke="#334155" strokeWidth="1.2" />

          {/* Connecting offset lines for dense European pins */}
          <line x1="430" y1="130" x2="495" y2="175" stroke="#334155" strokeDasharray="2,2" opacity="0.5" />
          <line x1="440" y1="170" x2="485" y2="135" stroke="#334155" strokeDasharray="2,2" opacity="0.5" />

          {/* Region Markers with Collision-Free Positions */}
          {Object.entries(REGION_COORDINATES).map(([key, reg]) => {
            const regionIncidents = regionMap.get(key) || [];
            if (regionIncidents.length === 0) return null;

            const isSelected = selectedCountry?.toLowerCase() === key;
            const isHovered = hoveredCountry?.toLowerCase() === key;
            const criticalCount = regionIncidents.filter((i) => i.severity === 'critical').length;
            const markerColor = criticalCount > 0 ? '#ef4444' : '#38bdf8';

            return (
              <g
                key={key}
                transform={`translate(${reg.cx},${reg.cy})`}
                style={{ cursor: 'pointer', transition: 'transform 0.2s ease' }}
                onMouseEnter={() => setHoveredCountry(key)}
                onMouseLeave={() => setHoveredCountry(null)}
                onClick={() => setSelectedCountry(isSelected ? null : key)}
              >
                {/* Outer Glow Ring */}
                <circle r={14 + Math.min(regionIncidents.length, 10)} fill={markerColor} opacity={isSelected || isHovered ? '0.4' : '0.15'}>
                  <animate attributeName="r" values="12;20;12" dur="3s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.3;0.1;0.3" dur="3s" repeatCount="indefinite" />
                </circle>

                {/* Main Marker Circle */}
                <circle
                  r={11 + Math.min(regionIncidents.length, 6)}
                  fill={markerColor}
                  stroke={isSelected || isHovered ? '#ffffff' : 'rgba(255,255,255,0.6)'}
                  strokeWidth={isSelected || isHovered ? 3 : 1.5}
                />

                {/* Count Badge */}
                <text y={4} fill="#ffffff" fontSize="11" fontWeight="700" textAnchor="middle" fontFamily="Inter">
                  {regionIncidents.length}
                </text>

                {/* Region Label Tag */}
                <rect
                  x="-35"
                  y="18"
                  width="70"
                  height="16"
                  rx="4"
                  fill="rgba(15, 23, 42, 0.85)"
                  stroke={isSelected ? 'var(--accent-cyan)' : 'rgba(255,255,255,0.15)'}
                  strokeWidth="1"
                />
                <text y={30} fill={isSelected ? 'var(--accent-cyan)' : '#e2e8f0'} fontSize="9" fontWeight="600" textAnchor="middle" fontFamily="Inter">
                  {reg.name.length > 12 ? `${reg.name.substring(0, 10)}..` : reg.name}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Hover Tooltip Card */}
        {hoverStats && (
          <div
            style={{
              position: 'absolute',
              top: '1.5rem',
              left: '1.5rem',
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid var(--accent-cyan)',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
              pointerEvents: 'none',
              backdropFilter: 'blur(10px)',
              zIndex: 10
            }}
          >
            <h4 style={{ fontSize: '0.9rem', color: '#f8fafc', fontWeight: 700, marginBottom: '0.3rem' }}>
              📍 {hoverStats.regionName}
            </h4>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
              <span>Total Incidents: <strong style={{ color: 'var(--accent-cyan)' }}>{hoverStats.count}</strong></span>
              <span>Critical Risk Events: <strong style={{ color: '#ef4444' }}>{hoverStats.criticalCount}</strong></span>
              {hoverStats.totalDamage > 0 && (
                <span>Est. Financial Impact: <strong style={{ color: '#34d399' }}>{formatFinancialDamage(hoverStats.totalDamage)}</strong></span>
              )}
            </div>
          </div>
        )}

        {/* Legend Overlay */}
        <div style={{ position: 'absolute', bottom: '1rem', right: '1rem', background: 'rgba(15, 23, 42, 0.85)', padding: '0.5rem 1rem', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.75rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444' }} /> Critical Risk
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#38bdf8' }} /> Standard Incident
          </span>
        </div>
      </div>

      {/* Region Incident Feed Grid */}
      <div className="detail-section">
        <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <MapPin size={16} style={{ color: 'var(--accent-cyan)' }} />
          Filtered Region: <span style={{ color: 'var(--accent-purple)' }}>{selectedCountry ? REGION_COORDINATES[selectedCountry.toLowerCase()]?.name || selectedCountry : 'All Global Regions'}</span>
          <span className="badge" style={{ backgroundColor: 'rgba(56, 189, 248, 0.2)', color: 'var(--accent-cyan)' }}>{activeIncidents.length} Events</span>
        </h3>

        <div className="grid-cards">
          {activeIncidents.map((inc) => (
            <div key={inc.incident_id} className={`incident-card card-${inc.severity}`} onClick={() => onSelectIncident(inc)}>
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
                <span className="details-link" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                  Details <ChevronRight size={14} />
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
