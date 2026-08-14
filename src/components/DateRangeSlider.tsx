import React, { useMemo } from 'react';

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
    // Find closest available date or use typed date
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

  const isSingleDay = selectedRange[0] === selectedRange[1];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', background: 'rgba(15, 23, 42, 0.9)', padding: '0.45rem 0.85rem', borderRadius: '8px', border: '1px solid var(--border-color)', minWidth: '320px', flexShrink: 0 }}>
      
      {/* TOP ROW: Explicit Date Picker Inputs + Presets */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
          {/* Start Date Input Box */}
          <input
            type="date"
            value={selectedRange[0]}
            min={availableDates[0]}
            max={selectedRange[1]}
            onChange={handleStartDatePicker}
            style={{
              background: 'rgba(0,0,0,0.4)',
              border: '1px solid var(--border-color)',
              borderRadius: '5px',
              color: 'var(--accent-cyan)',
              padding: '0.2rem 0.4rem',
              fontSize: '0.775rem',
              fontWeight: 600,
              fontFamily: 'inherit',
              colorScheme: 'dark',
              cursor: 'pointer'
            }}
          />

          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600 }}>to</span>

          {/* End Date Input Box */}
          <input
            type="date"
            value={selectedRange[1]}
            min={selectedRange[0]}
            max={availableDates[maxIndex]}
            onChange={handleEndDatePicker}
            style={{
              background: 'rgba(0,0,0,0.4)',
              border: '1px solid var(--border-color)',
              borderRadius: '5px',
              color: 'var(--accent-purple)',
              padding: '0.2rem 0.4rem',
              fontSize: '0.775rem',
              fontWeight: 600,
              fontFamily: 'inherit',
              colorScheme: 'dark',
              cursor: 'pointer'
            }}
          />
        </div>

        {/* Quick Presets Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
          <button
            onClick={setLatestDay}
            className="tab-button"
            style={{ padding: '0.15rem 0.4rem', fontSize: '0.7rem', height: 'auto', background: isSingleDay && selectedRange[0] === availableDates[maxIndex] ? 'rgba(56, 189, 248, 0.2)' : 'transparent' }}
            title="Jump to latest day"
          >
            Today
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
