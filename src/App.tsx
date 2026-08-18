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

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewType>('briefing');
  const [selectedIncident, setSelectedIncident] = useState<AIIncident | null>(null);

  const [rawIncidents, setRawIncidents] = useState<AIIncident[]>(() => incidentsData as unknown as AIIncident[]);
  const [edges, setEdges] = useState<GraphEdge[]>(edgesData as unknown as GraphEdge[]);

  const getYesterdayStr = (): string => {
    const d = new Date();
    d.setDate(d.getDate() - 1);
    return d.toISOString().split('T')[0];
  };

  // Continuous sorted dates ascending from min incident date through yesterday (today - 1 day)
  const availableDates = useMemo(() => {
    const datesSet = new Set<string>();
    rawIncidents.forEach((inc) => {
      if (inc.date) datesSet.add(inc.date);
    });
    const sortedRaw = Array.from(datesSet).sort((a, b) => a.localeCompare(b));
    const minDateStr = sortedRaw[0] || '2025-08-01';
    const yesterdayStr = getYesterdayStr();

    const result: string[] = [];
    const current = new Date(minDateStr + 'T00:00:00Z');
    const end = new Date(yesterdayStr + 'T00:00:00Z');

    if (current > end) {
      return sortedRaw.length > 0 ? sortedRaw : [yesterdayStr];
    }

    while (current <= end) {
      result.push(current.toISOString().split('T')[0]);
      current.setUTCDate(current.getUTCDate() + 1);
    }
    return result;
  }, [rawIncidents]);

  // Default dateRange to yesterday (today - 1 day, since today's run has not yet occurred)
  const [selectedRange, setSelectedRange] = useState<[string, string]>(() => {
    const yesterdayStr = getYesterdayStr();
    return [yesterdayStr, yesterdayStr];
  });

  // Keep selectedRange valid if availableDates change on Supabase load
  useEffect(() => {
    if (availableDates.length > 0) {
      const yesterdayStr = getYesterdayStr();
      const latestSelectable = availableDates.includes(yesterdayStr) ? yesterdayStr : availableDates[availableDates.length - 1];
      if (!selectedRange[0] || !selectedRange[1]) {
        setSelectedRange([latestSelectable, latestSelectable]);
      }
    }
  }, [availableDates]);

  useEffect(() => {
    if (isSupabaseConfigured) {
      console.log('Supabase credentials detected! Loading live dataset from Supabase PostgreSQL...');
      Promise.all([fetchIncidentsFromSupabase(), fetchEdgesFromSupabase()]).then(([dbIncidents, dbEdges]) => {
        if (dbIncidents.length > 0) {
          setRawIncidents(dbIncidents);
          const yesterdayStr = getYesterdayStr();
          setSelectedRange([yesterdayStr, yesterdayStr]);
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
