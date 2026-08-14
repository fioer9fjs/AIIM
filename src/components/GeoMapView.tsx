import React, { useEffect, useRef, useState, useMemo } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { AIIncident, formatFinancialDamage } from '../types/incident';
import { Globe, DollarSign, MapPin, ChevronRight, ShieldAlert } from 'lucide-react';

interface GeoMapViewProps {
  incidents: AIIncident[];
  onSelectIncident: (incident: AIIncident) => void;
}

// Real-world WGS84 Latitude / Longitude coordinates for key countries & regions
const REGION_COORDINATES: Record<string, { name: string; lat: number; lng: number }> = {
  'united states': { name: 'United States', lat: 37.0902, lng: -95.7129 },
  'usa': { name: 'United States', lat: 37.0902, lng: -95.7129 },
  'us': { name: 'United States', lat: 37.0902, lng: -95.7129 },
  'canada': { name: 'Canada', lat: 56.1304, lng: -106.3468 },
  'united kingdom': { name: 'United Kingdom', lat: 55.3781, lng: -3.4360 },
  'uk': { name: 'United Kingdom', lat: 55.3781, lng: -3.4360 },
  'france': { name: 'France', lat: 46.2276, lng: 2.2137 },
  'germany': { name: 'Germany', lat: 51.1657, lng: 10.4515 },
  'european union': { name: 'European Union', lat: 50.8503, lng: 4.3517 },
  'eu': { name: 'European Union', lat: 50.8503, lng: 4.3517 },
  'china': { name: 'China', lat: 35.8617, lng: 104.1954 },
  'japan': { name: 'Japan', lat: 36.2048, lng: 138.2529 },
  'india': { name: 'India', lat: 20.5937, lng: 78.9629 },
  'south korea': { name: 'South Korea', lat: 35.9078, lng: 127.7669 },
  'australia': { name: 'Australia', lat: -25.2744, lng: 133.7751 },
  'brazil': { name: 'Brazil', lat: -14.2350, lng: -51.9253 },
  'south africa': { name: 'South Africa', lat: -30.5595, lng: 22.9375 },
  'russia': { name: 'Russia', lat: 61.5240, lng: 105.3188 },
  'spain': { name: 'Spain', lat: 40.4637, lng: -3.7492 },
  'taiwan': { name: 'Taiwan', lat: 23.6978, lng: 120.9605 },
  'israel': { name: 'Israel', lat: 31.0461, lng: 34.8516 },
  'global': { name: 'Global / Multi-Region', lat: 20.0, lng: 0.0 }
};

export const GeoMapView: React.FC<GeoMapViewProps> = ({ incidents, onSelectIncident }) => {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersGroupRef = useRef<L.LayerGroup | null>(null);

  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);

  // Group incidents by region key
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

  // Initialize Leaflet Map instance with CartoDB Dark Matter tile layer
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [25.0, 10.0],
        zoom: 2,
        minZoom: 2,
        maxZoom: 8,
        zoomControl: true,
        attributionControl: true
      });

      // CartoDB Dark Matter Tile Layer (100% Free, Keyless, HD Dark Theme)
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
      }).addTo(map);

      markersGroupRef.current = L.layerGroup().addTo(map);
      mapInstanceRef.current = map;
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update Map Markers when incidents or selectedCountry changes
  useEffect(() => {
    if (!mapInstanceRef.current || !markersGroupRef.current) return;

    markersGroupRef.current.clearLayers();

    Object.entries(REGION_COORDINATES).forEach(([key, coords]) => {
      const regionIncidents = regionMap.get(key) || [];
      if (regionIncidents.length === 0) return;

      const isSelected = selectedCountry?.toLowerCase() === key;
      const criticalCount = regionIncidents.filter((i) => i.severity === 'critical').length;
      const markerColor = criticalCount > 0 ? '#ef4444' : '#38bdf8';
      const count = regionIncidents.length;

      // Custom Leaflet DivIcon with pulsing HTML badge
      const customIcon = L.divIcon({
        className: 'custom-leaflet-marker',
        html: `
          <div style="
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            width: ${28 + Math.min(count, 12)}px;
            height: ${28 + Math.min(count, 12)}px;
            background: ${markerColor};
            border: 2px solid ${isSelected ? '#ffffff' : 'rgba(255,255,255,0.7)'};
            border-radius: 50%;
            box-shadow: 0 0 15px ${markerColor};
            color: #ffffff;
            font-weight: 700;
            font-size: 12px;
            font-family: sans-serif;
            cursor: pointer;
            transition: transform 0.2s ease;
          ">
            ${count}
            <div style="
              position: absolute;
              bottom: -18px;
              white-space: nowrap;
              background: rgba(15, 23, 42, 0.9);
              color: ${isSelected ? '#38bdf8' : '#e2e8f0'};
              border: 1px solid rgba(255,255,255,0.2);
              padding: 1px 5px;
              border-radius: 4px;
              font-size: 10px;
              font-weight: 600;
            ">${coords.name}</div>
          </div>
        `,
        iconSize: [36, 36],
        iconAnchor: [18, 18]
      });

      const marker = L.marker([coords.lat, coords.lng], { icon: customIcon });

      const totalDamage = regionIncidents.reduce((sum, inc) => sum + (inc.financial_damage_usd || 0), 0);

      // Interactive Popup
      marker.bindPopup(`
        <div style="font-family: sans-serif; padding: 4px; color: #0f172a;">
          <h4 style="margin: 0 0 6px 0; font-size: 14px; font-weight: 700;">📍 ${coords.name}</h4>
          <p style="margin: 0 0 4px 0; font-size: 12px;">Incidents: <strong>${count}</strong></p>
          <p style="margin: 0 0 4px 0; font-size: 12px; color: #dc2626;">Critical Events: <strong>${criticalCount}</strong></p>
          ${totalDamage > 0 ? `<p style="margin: 0; font-size: 12px; color: #16a34a;">Est. Impact: <strong>${formatFinancialDamage(totalDamage)}</strong></p>` : ''}
        </div>
      `);

      marker.on('click', () => {
        setSelectedCountry(isSelected ? null : key);
      });

      markersGroupRef.current?.addLayer(marker);
    });
  }, [regionMap, selectedCountry]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header bar */}
      <div className="detail-section" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Globe size={20} style={{ color: 'var(--accent-cyan)' }} /> Global Geospatial Risk Map (CartoDB Dark Matter)
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Real-world OpenStreetMap GIS tiles showing global AI security breaches, regulatory actions, and financial impact.
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

      {/* Leaflet Map Viewport Container */}
      <div
        className="detail-section"
        style={{
          position: 'relative',
          padding: 0,
          borderRadius: '12px',
          overflow: 'hidden',
          border: '1px solid var(--border-color)',
          height: '520px'
        }}
      >
        <div ref={mapContainerRef} style={{ width: '100%', height: '100%', background: '#090d16' }} />
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
                  <span className="badge" style={{ backgroundColor: 'rgba(16, 185, 129, 0.2)', color: '#34d399', display: 'inline-flex', alignItems: 'center', gap: '0.2rem', fontWeight: 700 }}>
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
