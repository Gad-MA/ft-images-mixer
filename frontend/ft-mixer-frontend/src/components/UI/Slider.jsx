import React from 'react';

const Slider = ({ label, value, onChange, min = 0, max = 1, step = 0.01, disabled=false }) => {
  const percentage = ((value - min) / (max - min)) * 100;

  return (
    <div className="flex items-center space-x-2 w-full">
      {/* Value display - Before the slider */}
      <div className="text-xs font-mono text-text-muted w-10 text-right flex-shrink-0">
         {value.toFixed(2)}
      </div>
      <div className="relative flex-1 h-4 flex items-center">
          {/* Custom track background */}
        <div className="absolute bg-surface-lighter h-1 w-full rounded-full overflow-hidden">
           {/* Filled track */}
          <div
            className="h-full bg-primary"
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          // Tailwind styling for the native webkit slider thumb is tricky,
          // relying on basic appearance-none and custom track for simplicity here.
          // For perfect cross-browser styling matching the image exactly,
          // a library like Radix UI Slider is recommended.
          className="absolute w-full h-full opacity-0 cursor-pointer"
        />
         {/* Custom Thumb (Visual only, positioned by percentage) */}
         <div
            className={`absolute h-3 w-3 bg-text rounded-full shadow-sm pointer-events-none transform -translate-x-1/2 ${disabled ? 'bg-gray-500' : ''}`}
            style={{ left: `${percentage}%` }}
         ></div>
      </div>
    </div>
  );
};

export default Slider;