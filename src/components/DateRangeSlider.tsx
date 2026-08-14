import React, { useMemo } from 'react';
import { Calendar, RotateCcw } from 'lucide-react';

interface DateRangeSliderProps {
  availableDates: string[]; // Sorted ascending e.g. ["2025-08-01", ..., "2026-08-14"]
  selectedRange: [string, string]; // [startDate, endDate]
  onRangeChange: (range: [string, string]) => void;
}

export const DateRangeSlider: React.FC<DateRangeSliderProps> = ({
  availableDates,
  selectedRange,
  onRangeChange
}) => {
  if (!availableDates || availableDates.length === 0) {
    return null;
  }

  // Sorted indices mapping
  const minIndex = 0;
  const maxIndex = availableDates.length - 1;

  const startIndex = useMemo(() => {
    const idx = availableDates.indexOf(selectedRange[0]);
    return idx !== -1 ? idx : 0;
  }, [availableDates, selectedRange]);

  const endIndex = useMemo(() => {
    const idx = availableDates.indexOf(selectedRange[1]);
    return idx !== -1 ? idx : maxIndex;
  }, [availableDates, selectedRange, maxIndex]);

  const handleStartChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    const newStartIdx = Math.min(val, endIndex);
    onRangeChange([availableDates[newStartIdx], availableDates[endIndex]]);
  };

  const handleEndChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    const newEndIdx = Math.max(val, startIndex);
    onRangeChange([availableDates[startIndex], availableDates[newEndIdx]]);
  };

  // Presets
  const setLatestDay = () => {
    const latest = availableDates[maxIndex];
    onRangeChange([latest, latest]);
  };

  const setLast7Days = () => {
    const endIdx = maxIndex;
    const startIdx = Math.max(0, maxIndex - 6);
    onRangeChange([availableDates[startIdx], availableDates[endIdx]]);
  };

  const setLast30Days = () => {
    const endIdx = maxIndex;
    const startIdx = Math.max(0, maxIndex - 29);
    onRangeChange([availableDates[startIdx], availableDates[endIdx]]);
  };

  const setAllTime = () => {
    onRangeChange([availableDates[0], availableDates[maxIndex]]);
  };

  // Format label
  const isSingleDay = selectedRange[0] === selectedRange[1];

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', background: 'rgba(15, 23, 42, 0.75)', padding: '0.4rem 0.85rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
      {/* Date Icon & Formatted Label Badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.825rem', color: 'var(--text-main)', whiteSpace: 'nowrap' }}>
        <Calendar size={14} style={{ color: 'var(--accent-cyan)' }} />
        <span style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>
          {isSingleDay ? selectedRange[0] : `${selectedRange[0]} → ${selectedRange[1]}`}
        </span>
      </div>

      {/* Dual Slider Control */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', position: 'relative', width: '180px' }}>
        <input
          type="range"
          min={minIndex}
          max={maxIndex}
          value={startIndex}
          onChange={handleStartChange}
          style={{
            width: '100%',
            accentColor: 'var(--accent-cyan)',
            cursor: 'pointer',
            height: '4px'
          }}
          title={`Start Date: ${availableDates[startIndex]}`}
        />
        <input
          type="range"
          min={minIndex}
          max={maxIndex}
          value={endIndex}
          onChange={handleEndChange}
          style={{
            width: '100%',
            accentColor: 'var(--accent-purple)',
            cursor: 'pointer',
            height: '4px'
          }}
          title={`End Date: ${availableDates[endIndex]}`}
        />
      </div>

      {/* Quick Presets */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
        <button
          onClick={setLatestDay}
          className="tab-button"
          style={{ padding: '0.2rem 0.5rem', fontSize: '0.725rem', height: 'auto', background: isSingleDay && selectedRange[0] === availableDates[maxIndex] ? 'rgba(56, 189, 248, 0.2)' : 'transparent' }}
          title="Jump to latest day"
        >
          Today
        </button>
        <button
          onClick={setLast7Days}
          className="tab-button"
          style={{ padding: '0.2rem 0.5rem', fontSize: '0.725rem', height: 'auto' }}
          title="Select last 7 days"
        >
          7D
        </button>
        <button
          onClick={setLast30Days}
          className="tab-button"
          style={{ padding: '0.2rem 0.5rem', fontSize: '0.725rem', height: 'auto' }}
          title="Select last 30 days"
        >
          30D
        </button>
        <button
          onClick={setAllTime}
          className="tab-button"
          style={{ padding: '0.2rem 0.5rem', fontSize: '0.725rem', height: 'auto' }}
          title="Show all time"
        >
          All
        </button>
      </div>
    </div>
  );
};
