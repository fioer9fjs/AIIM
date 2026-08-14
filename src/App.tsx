import React, { useState, useEffect, useMemo } from 'react';
import { Header, ViewType } from './components/Header';
import { ExplorerView } from './components/ExplorerView';
import { GraphView } from './components/GraphView';
import { GeoMapView } from './components/GeoMapView';
import { AnalyticsView } from './components/AnalyticsView';
import { DailyBriefingView } from './components/DailyBriefingView';
import { AboutView } from './components/AboutView';
import { IncidentDetailDrawer } from './components/IncidentDetailDrawer';
import { AIIncident, GraphEdge } from './types/incident';
import { isSupabaseConfigured, fetchIncidentsFromSupabase, fetchEdgesFromSupabase } from './lib/supabase';

import incidentsData from './data/incidents.json';
import edgesData from './data/edges.json';

/**
 * Robust Client-Side Fuzzy Deduplicator.
 */
export function deduplicateIncidents(list: AIIncident[]): AIIncident[] {
  const result: AIIncident[] = [];
  
  for (const inc of list) {
    const titleClean = (inc.title || '').toLowerCase().trim();
    if (!titleClean) continue;

    const dupIndex = result.findIndex((existing) => {
      const exTitle = (existing.title || '').toLowerCase().trim();
      
      if (titleClean === exTitle) return true;
      if (titleClean.length > 20 && exTitle.length > 20) {
        if (titleClean.includes(exTitle) || exTitle.includes(titleClean)) return true;
      }

      const words1 = new Set(titleClean.split(/[^a-z0-9]+/).filter(w => w.length > 3));
      const words2 = new Set(exTitle.split(/[^a-z0-9]+/).filter(w => w.length > 3));
      
      if (words1.size === 0 || words2.size === 0) return false;
      
      let intersection = 0;
      words1.forEach(w => { if (words2.has(w)) intersection++; });
      const jaccard = intersection / Math.min(words1.size, words2.size);
      
      return jaccard >= 0.55;
    });

    if (dupIndex === -1) {
      result.push({ ...inc });
    } else {
      const canonical = result[dupIndex];
      const urls1 = canonical.source_urls || [];
      const urls2 = inc.source_urls || [];
      canonical.source_urls = Array.from(new Set([...urls1, ...urls2]));
      if ((inc.financial_damage_usd || 0) > (canonical.financial_damage_usd || 0)) {
        canonical.financial_damage_usd = inc.financial_damage_usd;
      }
    }
  }

  return result;
}

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewType>('briefing');
  const [selectedIncident, setSelectedIncident] = useState<AIIncident | null>(null);

  const [rawIncidents, setRawIncidents] = useState<AIIncident[]>(() => deduplicateIncidents(incidentsData as unknown as AIIncident[]));
  const [edges, setEdges] = useState<GraphEdge[]>(edgesData as unknown as GraphEdge[]);

  // Unique sorted dates ascending e.g. ["2025-08-01", ..., "2026-08-14"]
  const availableDates = useMemo(() => {
    const datesSet = new Set<string>();
    rawIncidents.forEach((inc) => {
      if (inc.date) datesSet.add(inc.date);
    });
    return Array.from(datesSet).sort((a, b) => a.localeCompare(b));
  }, [rawIncidents]);

  // Default dateRange to latest available single date [latestDate, latestDate]
  const [selectedRange, setSelectedRange] = useState<[string, string]>(() => {
    const latest = availableDates.length > 0 ? availableDates[availableDates.length - 1] : new Date().toISOString().split('T')[0];
    return [latest, latest];
  });

  // Keep selectedRange valid if availableDates change on Supabase load
  useEffect(() => {
    if (availableDates.length > 0) {
      const latest = availableDates[availableDates.length - 1];
      // Only set if range is uninitialized
      if (!selectedRange[0] || !selectedRange[1]) {
        setSelectedRange([latest, latest]);
      }
    }
  }, [availableDates]);

  useEffect(() => {
    if (isSupabaseConfigured) {
      console.log('Supabase credentials detected! Loading live dataset from Supabase PostgreSQL...');
      Promise.all([fetchIncidentsFromSupabase(), fetchEdgesFromSupabase()]).then(([dbIncidents, dbEdges]) => {
        if (dbIncidents.length > 0) {
          const dedupped = deduplicateIncidents(dbIncidents);
          setRawIncidents(dedupped);
          // Set initial range to latest date from DB
          const dates = Array.from(new Set(dedupped.map(i => i.date).filter(Boolean))).sort((a, b) => a.localeCompare(b));
          if (dates.length > 0) {
            const latest = dates[dates.length - 1];
            setSelectedRange([latest, latest]);
          }
        }
        if (dbEdges.length > 0) {
          setEdges(dbEdges);
        }
      });
    }
  }, []);

  // Filter incidents globally by selectedRange
  const filteredIncidents = useMemo(() => {
    const [start, end] = selectedRange;
    if (!start || !end) return rawIncidents;
    return rawIncidents.filter((inc) => inc.date >= start && inc.date <= end);
  }, [rawIncidents, selectedRange]);

  return (
    <div className="app-container">
      <Header
        currentView={currentView}
        onViewChange={setCurrentView}
        incidentCount={filteredIncidents.length}
        availableDates={availableDates}
        selectedRange={selectedRange}
        onRangeChange={setSelectedRange}
      />

      <main className="main-content">
        {currentView === 'briefing' && (
          <DailyBriefingView
            incidents={filteredIncidents}
            dateRange={selectedRange}
            onSelectIncident={setSelectedIncident}
          />
        )}
        {currentView === 'explorer' && (
          <ExplorerView incidents={filteredIncidents} onSelectIncident={setSelectedIncident} />
        )}
        {currentView === 'graph' && (
          <GraphView incidents={filteredIncidents} edges={edges} onSelectIncident={setSelectedIncident} />
        )}
        {currentView === 'map' && (
          <GeoMapView incidents={filteredIncidents} onSelectIncident={setSelectedIncident} />
        )}
        {currentView === 'analytics' && (
          <AnalyticsView incidents={filteredIncidents} onSelectIncident={setSelectedIncident} />
        )}
        {currentView === 'about' && (
          <AboutView />
        )}
      </main>

      <IncidentDetailDrawer
        incident={selectedIncident}
        edges={edges}
        allIncidents={rawIncidents}
        onClose={() => setSelectedIncident(null)}
        onSelectRelated={(relatedInc) => setSelectedIncident(relatedInc)}
      />
    </div>
  );
};

export default App;
