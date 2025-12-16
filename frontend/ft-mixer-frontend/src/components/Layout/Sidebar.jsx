import React from 'react';
import { RotateCcw } from 'lucide-react'; // Import Icon
import { useAppStore } from '../../store/useAppStore';
import Slider from '../UI/Slider';
import ProgressBar from '../UI/ProgressBar';

const Sidebar = () => {
  // Destructure resetWeights here
  const { mixerSettings, setMixerMode, setTargetOutput, setWeight, setRegionSetting, processingStatus, resetWeights } = useAppStore();
  const { mode, targetOutputPort, weights, region } = mixerSettings;

  const isMagPhase = mode === 'magnitude_phase';
  const component1Name = isMagPhase ? 'Magnitude' : 'Real';
  const component2Name = isMagPhase ? 'Phase' : 'Imaginary';
  const weights1 = weights[component1Name.toLowerCase()];
  const weights2 = weights[component2Name.toLowerCase()];

  return (
    <div className="panel-bg panel-border flex flex-col h-full">
      {/* Updated Header with Reset Button */}
      <div className="p-3 border-b border-border bg-surface-lighter flex justify-between items-center">
        <h2 className="font-bold text-text">Mixer Controls</h2>
        <button 
            onClick={resetWeights}
            className="p-1.5 rounded hover:bg-surface text-text-muted hover:text-primary transition-colors"
            title="Reset to Defaults"
        >
            <RotateCcw size={16} />
        </button>
      </div>

      <div className="p-4 flex flex-col space-y-6 overflow-y-auto flex-grow">
        {/* ... Rest of the component remains exactly the same ... */}
        
        {/* --- Top Section: Output & Mode Select --- */}
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-text-muted">Output To:</label>
                <select
                    className="bg-background border border-border rounded text-sm p-1 focus:border-primary outline-none"
                    value={targetOutputPort}
                    onChange={(e) => setTargetOutput(parseInt(e.target.value))}
                >
                    <option value={0}>Output 1</option>
                    <option value={1}>Output 2</option>
                </select>
            </div>

            <div className="flex bg-background rounded p-1 border border-border">
                <button
                    className={`flex-1 text-xs py-1 rounded ${isMagPhase ? 'bg-primary text-white' : 'text-text-muted hover:text-text'}`}
                    onClick={() => setMixerMode('magnitude_phase')}
                >
                    Mag / Phase
                </button>
                <button
                    className={`flex-1 text-xs py-1 rounded ${!isMagPhase ? 'bg-primary text-white' : 'text-text-muted hover:text-text'}`}
                    onClick={() => setMixerMode('real_imaginary')}
                >
                    Real / Imag
                </button>
            </div>
        </div>


        {/* --- Weights Section --- */}
        <div className="space-y-6">
            {/* Component 1 Weights */}
            <div className="space-y-2">
                 <h3 className="text-sm font-bold border-b border-border pb-1">{component1Name} Weights</h3>
                 {weights1.map((w, idx) => (
                     <div key={`${component1Name}-${idx}`} className="flex items-center space-x-2">
                         <span className="text-xs text-text-muted w-12">Img {idx + 1}</span>
                         <Slider value={w} onChange={(val) => setWeight(component1Name.toLowerCase(), idx, val)} />
                     </div>
                 ))}
            </div>

             {/* Component 2 Weights */}
            <div className="space-y-2">
                 <h3 className="text-sm font-bold border-b border-border pb-1">{component2Name} Weights</h3>
                 {weights2.map((w, idx) => (
                     <div key={`${component2Name}-${idx}`} className="flex items-center space-x-2">
                         <span className="text-xs text-text-muted w-12">Img {idx + 1}</span>
                         <Slider value={w} onChange={(val) => setWeight(component2Name.toLowerCase(), idx, val)} />
                     </div>
                 ))}
            </div>
        </div>

         {/* --- Region Mixer Section --- */}
        <div className="space-y-3 pt-4 border-t border-border">
             <div className="flex items-center justify-between">
                 <h3 className="text-sm font-bold">Region Filter</h3>
                 <input
                    type="checkbox"
                    checked={region.enabled}
                    onChange={(e) => setRegionSetting('enabled', e.target.checked)}
                    className="accent-primary"
                 />
             </div>

             <div className={`space-y-3 transition-opacity ${region.enabled ? 'opacity-100' : 'opacity-50 pointer-events-none'}`}>
                 <div className="flex text-xs bg-background rounded border border-border overflow-hidden">
                     <button
                        className={`flex-1 py-1 ${region.type === 'inner' ? 'bg-surface-lighter font-medium' : 'text-text-muted'}`}
                        onClick={() => setRegionSetting('type', 'inner')}
                     >
                         Inner (Low Freq)
                     </button>
                     <button
                        className={`flex-1 py-1 ${region.type === 'outer' ? 'bg-surface-lighter font-medium' : 'text-text-muted'}`}
                        onClick={() => setRegionSetting('type', 'outer')}
                     >
                         Outer (High Freq)
                     </button>
                 </div>
                 <Slider
                    label="Region Size"
                    value={region.size}
                    min={0.05} max={0.95}
                    onChange={(val) => setRegionSetting('size', val)}
                 />
             </div>
        </div>

      </div>

      {/* Footer Progress Bar */}
      <div className="p-3 bg-background border-t border-border flex flex-col space-y-2">
          <div className="flex justify-between text-xs text-text-muted">
              <span>Status:</span>
              <span>{processingStatus.isProcessing ? 'Processing...' : 'Idle'}</span>
          </div>
          <ProgressBar progress={processingStatus.progress} isProcessing={processingStatus.isProcessing} />
      </div>
    </div>
  );
};

export default Sidebar;