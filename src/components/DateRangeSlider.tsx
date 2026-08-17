import React, { useMemo } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface DateRangeSliderProps {
  availableDates: string[]; // Sorted ascending e.g. ["2025-08-01", ..., "2026-08-16"]
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

  const isSingleDay = selectedRange[0] === selectedRange[1];

  // 1-Day Step Handlers
  const stepPreviousDay = () => {
    const prevIdx = Math.max(0, startIndex - 1);
    const nextEndIdx = isSingleDay ? prevIdx : Math.max(prevIdx, endIndex);
    onRangeChange([availableDates[prevIdx], availableDates[nextEndIdx]]);
  };

  const stepNextDay = () => {
    const nextEndIdx = Math.min(maxIndex, endIndex + 1);
    const nextStartIdx = isSingleDay ? nextEndIdx : Math.min(nextEndIdx, startIndex);
    onRangeChange([availableDates[nextStartIdx], availableDates[nextEndIdx]]);
  };

  // Calculate percentages for visual track bar
  const startPercent = (startIndex / maxIndex) * 100;
  const endPercent = (endIndex / maxIndex) * 100;
  const activeWidth = Math.max(0, endPercent - startPercent);

  // Handlers for Slider Range Inputs
  const handleStartSlider = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    const newStartIdx = Math.min(val, endIndex);
    onRangeChange([availableDates[newStartIdx], availableDates[endIndex]]);
  };

  const handleEndSlider = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    const newEndIdx = Math.max(val, startIndex);
    onRangeChange([availableDates[startIndex], availableDates[newEndIdx]]);
  };

  // Handlers for Direct Date Pickers
  const handleStartDatePicker = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    if (!val) return;
    if (val <= selectedRange[1]) {
      onRangeChange([val, selectedRange[1]]);
    }
  };

  const handleEndDatePicker = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    if (!val) return;
    if (val >= selectedRange[0]) {
      onRangeChange([selectedRange[0], val]);
    }
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', background: 'rgba(15, 23, 42, 0.9)', padding: '0.45rem 0.85rem', borderRadius: '8px', border: '1px solid var(--border-color)', minWidth: '340px', flexShrink: 0 }}>
      
      {/* TOP ROW: Explicit Date Picker Inputs with 1-Day Arrow Controls + Presets */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          {/* Step 1 Day Backward Arrow */}
          <button
            onClick={stepPreviousDay}
            disabled={startIndex === 0}
            style={{
              border: '1px solid var(--border-color)',
              background: 'rgba(0,0,0,0.4)',
              color: startIndex === 0 ? 'rgba(255,255,255,0.2)' : 'var(--accent-cyan)',
              borderRadius: '5px',
              padding: '0.2rem 0.35rem',
              cursor: startIndex === 0 ? 'not-allowed' : 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.15s ease'
            }}
            title="Step 1 day backward (<)"
          >
            <ChevronLeft size={14} />
          </button>

          {/* Start Date Input Box with Strict YYYY-MM-DD Text Overlay */}
          <div style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
            <span
              style={{
                background: 'rgba(0,0,0,0.5)',
                border: '1px solid var(--border-color)',
                borderRadius: '5px',
                color: 'var(--accent-cyan)',
                padding: '0.2rem 0.45rem',
                fontSize: '0.775rem',
                fontWeight: 600,
                fontFamily: 'monospace',
                letterSpacing: '0.03em',
                pointerEvents: 'none',
                userSelect: 'none'
              }}
            >
              {selectedRange[0]}
            </span>
            <input
              type="date"
              value={selectedRange[0]}
              min={availableDates[0]}
              max={selectedRange[1]}
              onChange={handleStartDatePicker}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                opacity: 0,
                cursor: 'pointer',
                colorScheme: 'dark'
              }}
            />
          </div>

          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600 }}>to</span>

          {/* End Date Input Box with Strict YYYY-MM-DD Text Overlay */}
          <div style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
            <span
              style={{
                background: 'rgba(0,0,0,0.5)',
                border: '1px solid var(--border-color)',
                borderRadius: '5px',
                color: 'var(--accent-purple)',
                padding: '0.2rem 0.45rem',
                fontSize: '0.775rem',
                fontWeight: 600,
                fontFamily: 'monospace',
                letterSpacing: '0.03em',
                pointerEvents: 'none',
                userSelect: 'none'
              }}
            >
              {selectedRange[1]}
            </span>
            <input
              type="date"
              value={selectedRange[1]}
              min={selectedRange[0]}
              max={availableDates[maxIndex]}
              onChange={handleEndDatePicker}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                opacity: 0,
                cursor: 'pointer',
                colorScheme: 'dark'
              }}
            />
          </div>

          {/* Step 1 Day Forward Arrow */}
          <button
            onClick={stepNextDay}
            disabled={endIndex === maxIndex}
            style={{
              border: '1px solid var(--border-color)',
              background: 'rgba(0,0,0,0.4)',
              color: endIndex === maxIndex ? 'rgba(255,255,255,0.2)' : 'var(--accent-purple)',
              borderRadius: '5px',
              padding: '0.2rem 0.35rem',
              cursor: endIndex === maxIndex ? 'not-allowed' : 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.15s ease'
            }}
            title="Step 1 day forward (>)"
          >
            <ChevronRight size={14} />
          </button>
        </div>

        {/* Quick Presets Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
          <button
            onClick={setLatestDay}
            className="tab-button"
            style={{ padding: '0.15rem 0.4rem', fontSize: '0.7rem', height: 'auto', background: isSingleDay && selectedRange[0] === availableDates[maxIndex] ? 'rgba(56, 189, 248, 0.2)' : 'transparent' }}
            title="Jump to latest completed day (Yesterday)"
          >
            Yesterday
          </button>
          <button
            onClick={setLast7Days}
            className="tab-button"
            style={{ padding: '0.15rem 0.4rem', fontSize: '0.7rem', height: 'auto' }}
            title="Select last 7 days"
          >
            7D
          </button>
          <button
            onClick={setLast30Days}
            className="tab-button"
            style={{ padding: '0.15rem 0.4rem', fontSize: '0.7rem', height: 'auto' }}
            title="Select last 30 days"
          >
            30D
          </button>
          <button
            onClick={setAllTime}
            className="tab-button"
            style={{ padding: '0.15rem 0.4rem', fontSize: '0.7rem', height: 'auto' }}
            title="Show all time"
          >
            All
          </button>
        </div>

      </div>

      {/* BOTTOM ROW: Visual Double-Slider Timeline Track */}
      <div style={{ position: 'relative', width: '100%', height: '14px', display: 'flex', alignItems: 'center' }}>
        {/* Background Track Line */}
        <div style={{ position: 'absolute', width: '100%', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px' }} />
        
        {/* Highlighted Active Range Bar */}
        <div
          style={{
            position: 'absolute',
            left: `${startPercent}%`,
            width: `${activeWidth}%`,
            height: '4px',
            background: 'linear-gradient(to right, var(--accent-cyan), var(--accent-purple))',
            borderRadius: '2px',
            zIndex: 1
          }}
        />

        {/* Start Handle Input */}
        <input
          type="range"
          min={minIndex}
          max={maxIndex}
          value={startIndex}
          onChange={handleStartSlider}
          style={{
            position: 'absolute',
            width: '100%',
            appearance: 'none',
            background: 'transparent',
            pointerEvents: 'none',
            zIndex: 3,
            margin: 0
          }}
          title={`Start Date: ${availableDates[startIndex]}`}
        />

        {/* End Handle Input */}
        <input
          type="range"
          min={minIndex}
          max={maxIndex}
          value={endIndex}
          onChange={handleEndSlider}
          style={{
            position: 'absolute',
            width: '100%',
            appearance: 'none',
            background: 'transparent',
            pointerEvents: 'none',
            zIndex: 4,
            margin: 0
          }}
          title={`End Date: ${availableDates[endIndex]}`}
        />
      </div>

    </div>
  );
};
