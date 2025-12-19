import React, { useRef, useState } from 'react';
import { Upload, Image as ImageIcon } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

const ImageCanvas = ({ id, type, imageState }) => {
  // Use the new setBrightnessContrast action
  const { loadImage, setBrightnessContrast } = useAppStore();
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  
  // Store both the mouse position AND the initial values when drag starts
  const dragStart = useRef({ x: 0, y: 0, initialB: 0, initialC: 1 });

  const handleDoubleClick = () => {
    if (type === 'input') {
      fileInputRef.current?.click();
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      loadImage(id, file);
    }
  };

  // --- Brightness/Contrast Drag Handlers ---
  const handleMouseDown = (e) => {
    if (!imageState.hasImage) return;
    setIsDragging(true);
    // Capture STARTING values
    dragStart.current = { 
        x: e.clientX, 
        y: e.clientY,
        initialB: imageState.brightness,
        initialC: imageState.contrast
    };
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    
    // Calculate how far we moved from the start
    const deltaX = e.clientX - dragStart.current.x;
    const deltaY = e.clientY - dragStart.current.y;

    // Calculate Target Values based on Initial + Delta
    // Sensitivity: 0.5 for brightness, 0.01 for contrast
    const targetBrightness = dragStart.current.initialB + (deltaX * 0.5);
    const targetContrast = dragStart.current.initialC + (-deltaY * 0.01);

    // Send exact target values to store
    setBrightnessContrast(id, type, targetBrightness, targetContrast);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  return (
    <div
      className="flex-grow relative bg-background overflow-hidden cursor-crosshair group"
      onDoubleClick={handleDoubleClick}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        accept="image/png, image/jpeg, image/jpg, image/webp"
        onChange={handleFileChange}
      />

      {imageState.isLoading && (
         <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
             <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
         </div>
      )}

      {!imageState.hasImage ? (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-text-muted transition-colors group-hover:text-text">
          {type === 'input' ? <Upload size={48} className="mb-2 opacity-50" /> : <ImageIcon size={48} className="mb-2 opacity-50"/>}
          <p className="text-sm font-medium">
            {type === 'input' ? "Double-click to upload" : "Output Pending..."}
          </p>
        </div>
      ) : (
        <img
          src={imageState.src}
          alt={`${type} ${id}`}
          className="w-full h-full object-contain pointer-events-none select-none"
          style={{ filter: `brightness(${100 + imageState.brightness}%) contrast(${imageState.contrast})` }}
        />
      )}

      {isDragging && (
          <div className="absolute bottom-2 left-2 bg-black/70 text-xs p-1 rounded text-text-muted pointer-events-none">
              B: {Math.round(imageState.brightness)}, C: {imageState.contrast.toFixed(2)}
          </div>
      )}
    </div>
  );
};

export default ImageCanvas;