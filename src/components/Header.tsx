import React from 'react';
import { ShieldAlert, Network, Table, BarChart3 } from 'lucide-react';

interface HeaderProps {
  currentView: 'explorer' | 'graph' | 'analytics';
  onViewChange: (view: 'explorer' | 'graph' | 'analytics') => void;
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
            Knowledge Graph & Safety Analytics • {incidentCount} Records Ingested
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
          className={`tab-button ${currentView === 'analytics' ? 'active' : ''}`}
          onClick={() => onViewChange('analytics')}
        >
          <BarChart3 size={16} /> Analytics
        </button>
      </div>
    </header>
  );
};
