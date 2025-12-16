import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import ImageCanvas from './ImageCanvas';

const COMPONENT_OPTIONS = ['Original', 'Magnitude', 'Phase', 'Real', 'Imaginary'];

const ImageViewerContainer = ({ id, type, title }) => {
  const imageState = useAppStore(state =>
    type === 'input' ? state.inputImages[id] : state.outputImages[id]
  );
  const setComponentType = useAppStore(state => state.setComponentType);

  return (
    <div className="flex flex-col h-full panel-bg panel-border">
      {/* Header */}
      <div className="flex items-center justify-between p-2 border-b border-border bg-surface-lighter h-10">
        <h3 className="font-semibold text-sm italic">{title}</h3>
        <select
          className="bg-background border border-border rounded text-xs p-1 focus:border-primary outline-none"
          value={imageState.componentType}
          onChange={(e) => setComponentType(id, type, e.target.value)}
          disabled={!imageState.hasImage}
        >
          {COMPONENT_OPTIONS.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      </div>

      {/* Canvas Area */}
      <ImageCanvas id={id} type={type} imageState={imageState} />
    </div>
  );
};

export default ImageViewerContainer;