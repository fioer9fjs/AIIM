import React from 'react';
import { ShieldAlert, Network, Table, BarChart3, Globe, FileText, Info } from 'lucide-react';
import { DateRangeSlider } from './DateRangeSlider';

export type ViewType = 'explorer' | 'graph' | 'map' | 'analytics' | 'briefing' | 'about';

interface HeaderProps {
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
  incidentCount: number;
  availableDates: string[];
  selectedRange: [string, string];
  onRangeChange: (range: [string, string]) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentView,
  onViewChange,
  incidentCount,
  availableDates,
  selectedRange,
  onRangeChange
}) => {
  return (
    <header className="header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', flexWrap: 'wrap', flex: '1 1 auto', minWidth: 0 }}>
        {/* Logo Group */}
        <div
          className="logo-group"
          onClick={() => onViewChange('briefing')}
          style={{ cursor: 'pointer', userSelect: 'none' }}
          title="Go to Home Briefing"
        >
          <ShieldAlert className="logo-icon" />
          <div>
            <h1 className="logo-title">Global AI Incident Monitor</h1>
            <span style={{ fontSize: '0.725rem', color: 'var(--text-dim)', display: 'block', lineHeight: 1.2 }}>
              Multi-Source Intelligence • {incidentCount} Records
            </span>
          </div>
        </div>

        {/* Global Date Range Slider Widget */}
        <DateRangeSlider
          availableDates={availableDates}
          selectedRange={selectedRange}
          onRangeChange={onRangeChange}
        />
      </div>

      <div className="nav-tabs">
        <button
          className={`tab-button ${currentView === 'briefing' ? 'active' : ''}`}
          onClick={() => onViewChange('briefing')}
        >
          <FileText size={16} /> Daily Briefing
        </button>
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
          className={`tab-button ${currentView === 'about' ? 'active' : ''}`}
          onClick={() => onViewChange('about')}
        >
          <Info size={16} /> About & Methodology
        </button>
      </div>
    </header>
  );
};
