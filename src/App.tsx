import React, { useState, useEffect } from 'react';
import { Header, ViewType } from './components/Header';
import { ExplorerView } from './components/ExplorerView';
import { GraphView } from './components/GraphView';
import { GeoMapView } from './components/GeoMapView';
import { AnalyticsView } from './components/AnalyticsView';
import { DailyBriefingView } from './components/DailyBriefingView';
import { IncidentDetailDrawer } from './components/IncidentDetailDrawer';
import { AIIncident, GraphEdge } from './types/incident';
import { isSupabaseConfigured, fetchIncidentsFromSupabase, fetchEdgesFromSupabase } from './lib/supabase';

import incidentsData from './data/incidents.json';
import edgesData from './data/edges.json';

export const App: React.FC = () => {
  // Set default home view to 'briefing'
  const [currentView, setCurrentView] = useState<ViewType>('briefing');
  const [selectedIncident, setSelectedIncident] = useState<AIIncident | null>(null);

  const [incidents, setIncidents] = useState<AIIncident[]>(incidentsData as AIIncident[]);
  const [edges, setEdges] = useState<GraphEdge[]>(edgesData as GraphEdge[]);

  useEffect(() => {
    if (isSupabaseConfigured) {
      console.log('Supabase credentials detected! Loading live dataset from Supabase PostgreSQL...');
      Promise.all([fetchIncidentsFromSupabase(), fetchEdgesFromSupabase()]).then(([dbIncidents, dbEdges]) => {
        if (dbIncidents.length > 0) {
          setIncidents(dbIncidents);
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
