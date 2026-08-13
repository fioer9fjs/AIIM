import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ExplorerView } from './components/ExplorerView';
import { GraphView } from './components/GraphView';
import { AnalyticsView } from './components/AnalyticsView';
import { IncidentDetailDrawer } from './components/IncidentDetailDrawer';
import { AIIncident, GraphEdge } from './types/incident';
import { isSupabaseConfigured, fetchIncidentsFromSupabase, fetchEdgesFromSupabase } from './lib/supabase';

import incidentsData from './data/incidents.json';
import edgesData from './data/edges.json';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'explorer' | 'graph' | 'analytics'>('explorer');
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
        {currentView === 'explorer' && (
          <ExplorerView incidents={incidents} onSelectIncident={setSelectedIncident} />
        )}
        {currentView === 'graph' && (
          <GraphView incidents={incidents} edges={edges} onSelectIncident={setSelectedIncident} />
        )}
        {currentView === 'analytics' && <AnalyticsView incidents={incidents} />}
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
