import React from 'react';
import { RotateCcw } from 'lucide-react'; // Import Icon
import { useAppStore } from '../../store/useAppStore';
import Slider from '../UI/Slider';
import ProgressBar from '../UI/ProgressBar';

const Sidebar = () => {
  const [activeTab, setActiveTab] = React.useState('mixer');
  
  // Destructure resetWeights here
  const { mixerSettings, setMixerMode, setTargetOutput, setWeight, setRegionSetting, setUnifiedRegion, setComponentRegionType, processingStatus, resetWeights } = useAppStore();
  const { mode, targetOutputPort, weights, region } = mixerSettings;

  const isMagPhase = mode === 'magnitude_phase';
  const component1Name = isMagPhase ? 'Magnitude' : 'Real';
  const component2Name = isMagPhase ? 'Phase' : 'Imaginary';
  const weights1 = weights[component1Name.toLowerCase()];
  const weights2 = weights[component2Name.toLowerCase()];

  return (
    <div className="panel-bg panel-border flex flex-col h-full">
      {/* Updated Header with Tabs */}
      <div className="p-3 border-b border-border bg-surface-lighter">
        <div className="flex justify-between items-center mb-2">
          <h2 className="font-bold text-text">Controls</h2>
          <button 
              onClick={resetWeights}
              className="p-1.5 rounded hover:bg-surface text-text-muted hover:text-primary transition-colors"
              title="Reset to Defaults"
          >
              <RotateCcw size={16} />
          </button>
        </div>
        
        {/* Tab Navigation */}
        <div className="flex gap-1 bg-background rounded p-1">
          <button
            className={`flex-1 text-xs py-1.5 rounded transition-colors ${
              activeTab === 'mixer' ? 'bg-primary text-white' : 'text-text-muted hover:text-text'
            }`}
            onClick={() => setActiveTab('mixer')}
          >
            Normal Mix
          </button>
          <button
            className={`flex-1 text-xs py-1.5 rounded transition-colors ${
              activeTab === 'region' ? 'bg-primary text-white' : 'text-text-muted hover:text-text'
            }`}
            onClick={() => setActiveTab('region')}
          >
            Region Filter
          </button>
        </div>
      </div>

      <div className="p-4 flex flex-col space-y-6 overflow-y-auto flex-grow">
        {/* --- Normal Mix Tab --- */}
        {activeTab === 'mixer' && (
          <div className="space-y-6">
            {/* Top Section: Output & Mode Select */}
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

            {/* Weights Section */}
            <div className="space-y-6">
                {/* Component 1 Weights */}
                <div className="space-y-2">
                     <h3 className="text-sm font-bold border-b border-border pb-1">{component1Name} Weights</h3>
                     {weights1.map((w, idx) => (
                         <div key={`${component1Name}-${idx}`} className="flex items-center space-x-2">
                             <span className="text-xs text-text-muted w-10 flex-shrink-0">Img {idx + 1}</span>
                             <Slider value={w} onChange={(val) => setWeight(component1Name.toLowerCase(), idx, val)} />
                         </div>
                     ))}
                </div>

                 {/* Component 2 Weights */}
                <div className="space-y-2">
                     <h3 className="text-sm font-bold border-b border-border pb-1">{component2Name} Weights</h3>
                     {weights2.map((w, idx) => (
                         <div key={`${component2Name}-${idx}`} className="flex items-center space-x-2">
                             <span className="text-xs text-text-muted w-10 flex-shrink-0">Img {idx + 1}</span>
                             <Slider value={w} onChange={(val) => setWeight(component2Name.toLowerCase(), idx, val)} />
                         </div>
                     ))}
                </div>
            </div>
          </div>
        )}

        {/* --- Region Filter Tab --- */}
        {activeTab === 'region' && (
          <div className="space-y-6">
            {/* Enable/Disable Region */}
            <div className="flex items-center justify-between">
                 <h3 className="text-sm font-bold">Enable Region Filter</h3>
                 <input
                    type="checkbox"
                    checked={region.enabled}
                    onChange={(e) => setRegionSetting('enabled', e.target.checked)}
                    className="accent-primary w-4 h-4"
                 />
             </div>

             {/* Region Mode Selector */}
             <div className={`transition-opacity ${region.enabled ? 'opacity-100' : 'opacity-50 pointer-events-none'}`}>
                 <label className="text-sm font-medium text-text-muted block mb-2">Region Mode</label>
                 <div className="flex bg-surface rounded overflow-hidden border border-border">
                   <button
                     className={`flex-1 px-3 py-2 text-xs ${region.mode === 'unified' ? 'bg-primary text-white' : 'text-text-muted hover:text-text hover:bg-surface-lighter'}`}
                     onClick={() => setRegionSetting('mode', 'unified')}
                   >Unified (Synced)</button>
                   <button
                     className={`flex-1 px-3 py-2 text-xs ${region.mode === 'independent' ? 'bg-primary text-white' : 'text-text-muted hover:text-text hover:bg-surface-lighter'}`}
                     onClick={() => setRegionSetting('mode', 'independent')}
                   >Independent</button>
                 </div>
                 <p className="text-xs text-text-muted mt-1">
                   {region.mode === 'unified' ? 'All images share the same region' : 'Each image has its own region'}
                 </p>
             </div>

             {/* Region Controls - Only show for unified mode */}
             {region.mode === 'unified' && (
               <div className={`space-y-4 transition-opacity ${region.enabled ? 'opacity-100' : 'opacity-50 pointer-events-none'}`}>
                 <div>
                   <label className="text-sm font-medium text-text-muted block mb-2">Per-Component Region Inclusion</label>
                   <div className="grid grid-cols-2 gap-2 text-xs">
                     {['magnitude', 'phase', 'real', 'imaginary'].map((comp) => (
                       <div key={comp} className="flex items-center justify-between bg-background rounded border border-border p-2">
                         <div className="text-xs text-text-muted capitalize">{comp}</div>
                         <div className="flex bg-surface rounded overflow-hidden text-xs">
                           <button
                             className={`px-2 py-1 ${region.unified[comp] === 'inner' ? 'bg-primary text-white' : 'text-text-muted hover:text-text'}`}
                             onClick={() => setUnifiedRegion(comp, 'inner')}
                           >Inner</button>
                           <button
                             className={`px-2 py-1 ${region.unified[comp] === 'outer' ? 'bg-primary text-white' : 'text-text-muted hover:text-text'}`}
                             onClick={() => setUnifiedRegion(comp, 'outer')}
                           >Outer</button>
                         </div>
                       </div>
                     ))}
                   </div>
                 </div>
                 
                 <div className="bg-surface-lighter border border-border rounded p-3 text-xs text-text-muted">
                   <p className="mb-2"><strong>Drag</strong> the region on any image to move it</p>
                   <p className="mb-2"><strong>Resize</strong> by dragging the corner handles</p>
                   <p className="mb-2"><strong>Inner:</strong> Mix only low frequencies (center)</p>
                   <p><strong>Outer:</strong> Mix only high frequencies (edges)</p>
                 </div>
               </div>
             )}

             {/* Independent Mode Info */}
             {region.mode === 'independent' && region.enabled && (
               <div className="bg-surface-lighter border border-border rounded p-3 text-xs text-text-muted space-y-2">
                 <p><strong>Independent Mode:</strong> Each image has its own region</p>
                 <p>• <strong>Drag</strong> each region to reposition</p>
                 <p>• <strong>Resize</strong> using corner handles</p>
                 <p>• Configure per-component settings on each image</p>
               </div>
             )}
          </div>
        )}

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