import React from 'react';
import { ShieldAlert, Network, Table, BarChart3, Globe, FileText } from 'lucide-react';

export type ViewType = 'explorer' | 'graph' | 'map' | 'analytics' | 'briefing';

interface HeaderProps {
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
  incidentCount: number;
}

export const Header: React.FC<HeaderProps> = ({ currentView, onViewChange, incidentCount }) => {
  return (
    <header className="header">
      <div className="logo-group">
        <ShieldAlert className="logo-icon" />
        <div>
          <h1 className="logo-title">Global AI Incident Monitor</h1>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Safety Analytics & Multi-Source Intelligence • {incidentCount} Records Ingested
          </span>
        </div>
      </div>

      <div className="nav-tabs">
        <button
          className={`tab-button ${currentView === 'explorer' ? 'active' : ''}`}
          onClick={() => onViewChange('explorer')}
        >
          <Table size={16} /> Explorer & Feed
        </button>
        <button
          className={`tab-button ${currentView === 'graph' ? 'active' : ''}`}
          onClick={() => onViewChange('graph')}
        >
          <Network size={16} /> Knowledge Graph
        </button>
        <button
          className={`tab-button ${currentView === 'map' ? 'active' : ''}`}
          onClick={() => onViewChange('map')}
        >
          <Globe size={16} /> World Map
        </button>
        <button
          className={`tab-button ${currentView === 'analytics' ? 'active' : ''}`}
          onClick={() => onViewChange('analytics')}
        >
          <BarChart3 size={16} /> Analytics
        </button>
        <button
          className={`tab-button ${currentView === 'briefing' ? 'active' : ''}`}
          onClick={() => onViewChange('briefing')}
        >
          <FileText size={16} /> Daily Briefing
        </button>
      </div>
    </header>
  );
};
