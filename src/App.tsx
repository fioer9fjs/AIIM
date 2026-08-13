import React, { useState } from 'react';
import { Header } from './components/Header';
import { ExplorerView } from './components/ExplorerView';
import { GraphView } from './components/GraphView';
import { AnalyticsView } from './components/AnalyticsView';
import { IncidentDetailDrawer } from './components/IncidentDetailDrawer';
import { AIIncident, GraphEdge } from './types/incident';

import incidentsData from './data/incidents.json';
import edgesData from './data/edges.json';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'explorer' | 'graph' | 'analytics'>('explorer');
  const [selectedIncident, setSelectedIncident] = useState<AIIncident | null>(null);

  const incidents = incidentsData as AIIncident[];
  const edges = edgesData as GraphEdge[];

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
