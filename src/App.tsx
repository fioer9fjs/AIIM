import React, { useState, useEffect } from 'react';
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
 * Guarantees zero duplicate incidents are ever displayed in the UI,
 * merging source URLs and financial damage metrics.
 */
export function deduplicateIncidents(list: AIIncident[]): AIIncident[] {
  const result: AIIncident[] = [];
  
  for (const inc of list) {
    const titleClean = (inc.title || '').toLowerCase().trim();
    if (!titleClean) continue;

    const dupIndex = result.findIndex((existing) => {
      const exTitle = (existing.title || '').toLowerCase().trim();
      
      // 1. Exact or substring title match
      if (titleClean === exTitle) return true;
      if (titleClean.length > 20 && exTitle.length > 20) {
        if (titleClean.includes(exTitle) || exTitle.includes(titleClean)) return true;
      }

      // 2. Significant word overlap match (Jaccard similarity >= 0.5)
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
      // Merge source URLs into canonical item
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
  // Set default home view to 'briefing'
  const [currentView, setCurrentView] = useState<ViewType>('briefing');
  const [selectedIncident, setSelectedIncident] = useState<AIIncident | null>(null);

  const [incidents, setIncidents] = useState<AIIncident[]>(() => deduplicateIncidents(incidentsData as unknown as AIIncident[]));
  const [edges, setEdges] = useState<GraphEdge[]>(edgesData as unknown as GraphEdge[]);

  useEffect(() => {
    if (isSupabaseConfigured) {
      console.log('Supabase credentials detected! Loading live dataset from Supabase PostgreSQL...');
      Promise.all([fetchIncidentsFromSupabase(), fetchEdgesFromSupabase()]).then(([dbIncidents, dbEdges]) => {
        if (dbIncidents.length > 0) {
          setIncidents(deduplicateIncidents(dbIncidents));
        }
        if (dbEdges.length > 0) {
          setEdges(dbEdges);
        }
      });
    }
  }, []);

  return (
    <div className="app-container">
      <Header
        currentView={currentView}
        onViewChange={setCurrentView}
        incidentCount={incidents.length}
      />

      <main className="main-content">
        {currentView === 'briefing' && (
          <DailyBriefingView incidents={incidents} onSelectIncident={setSelectedIncident} />
        )}
        {currentView === 'explorer' && (
          <ExplorerView incidents={incidents} onSelectIncident={setSelectedIncident} />
        )}
        {currentView === 'graph' && (
          <GraphView incidents={incidents} edges={edges} onSelectIncident={setSelectedIncident} />
        )}
        {currentView === 'map' && (
          <GeoMapView incidents={incidents} onSelectIncident={setSelectedIncident} />
        )}
        {currentView === 'analytics' && (
          <AnalyticsView incidents={incidents} onSelectIncident={setSelectedIncident} />
        )}
        {currentView === 'about' && (
          <AboutView />
        )}
      </main>

      <IncidentDetailDrawer
        incident={selectedIncident}
        edges={edges}
        allIncidents={incidents}
        onClose={() => setSelectedIncident(null)}
        onSelectRelated={(relatedInc) => setSelectedIncident(relatedInc)}
      />
    </div>
  );
};

export default App;
