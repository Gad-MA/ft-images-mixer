import React, { useEffect, useRef } from 'react';
import { Upload, Image as ImageIcon, X } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { api } from '../../utils/api';

const ORIGINAL_OPTIONS = ['Original', 'Greyscale'];
const FT_COMPONENT_OPTIONS = ['Magnitude', 'Phase', 'Real', 'Imaginary'];

const ImagePairViewer = ({ id, title }) => {
  const imageState = useAppStore(state => state.inputImages[id]);
  const loadImage = useAppStore(state => state.loadImage);
  const clearImage = useAppStore(state => state.clearImage);
  const setBrightnessContrast = useAppStore(state => state.setBrightnessContrast);
  const setFtBrightnessContrast = useAppStore(state => state.setFtBrightnessContrast);
  
  const fileInputRef = useRef(null);
  
  // Store separate states for original and FT views
  const [originalView, setOriginalView] = React.useState('Original');
  const [ftView, setFtView] = React.useState('Magnitude');
  
  // Store separate image sources for each view
  const [originalSrc, setOriginalSrc] = React.useState(null);
  const [ftSrc, setFtSrc] = React.useState(null);
  const containerFtRef = useRef(null);
  
  // Drag states for brightness/contrast
  const [isDraggingOriginal, setIsDraggingOriginal] = React.useState(false);
  const [isDraggingFt, setIsDraggingFt] = React.useState(false);
  const dragStartOriginal = useRef({ x: 0, y: 0, initialB: 0, initialC: 1 });
  const dragStartFt = useRef({ x: 0, y: 0, initialB: 0, initialC: 1 });
  
  // Interaction mode for FT viewport (brightness/contrast vs region control)
  const [ftInteractionMode, setFtInteractionMode] = React.useState('region'); // 'region' or 'brightness'

  // Fetch views when component type changes or image is loaded
  useEffect(() => {
    if (!imageState.hasImage) {
      // Clear sources when no image
      setOriginalSrc(null);
      return;
    }
    
    const fetchOriginalView = async () => {
      try {
        if (originalView === 'Greyscale') {
          // Convert original colored image to greyscale in frontend
          const result = await api.getView(id, 'input', 'Original');
          if (result.success) {
            // Convert to greyscale using canvas
            const img = new Image();
            img.onload = () => {
              const canvas = document.createElement('canvas');
              canvas.width = img.width;
              canvas.height = img.height;
              const ctx = canvas.getContext('2d');
              ctx.drawImage(img, 0, 0);
              
              const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
              const data = imageData.data;
              
              // Convert to greyscale
              for (let i = 0; i < data.length; i += 4) {
                const grey = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
                data[i] = grey;
                data[i + 1] = grey;
                data[i + 2] = grey;
              }
              
              ctx.putImageData(imageData, 0, 0);
              setOriginalSrc(canvas.toDataURL());
            };
            img.src = result.imageUrl;
          }
        } else {
          // Fetch original colored image
          const result = await api.getView(id, 'input', 'Original');
          if (result.success) {
            setOriginalSrc(result.imageUrl);
          }
        }
      } catch (err) {
        console.error('Failed to fetch original view:', err);
      }
    };
    
    fetchOriginalView();
  }, [imageState.hasImage, imageState.src, originalView, id]);

  useEffect(() => {
    if (!imageState.hasImage) {
      // Clear FT source when no image
      setFtSrc(null);
      return;
    }
    
    const fetchFtView = async () => {
      try {
        const apiComponent = ftView.toLowerCase();
        const result = await api.getView(id, 'input', apiComponent);
        if (result.success) {
          setFtSrc(result.imageUrl);
        }
      } catch (err) {
        console.error('Failed to fetch FT view:', err);
      }
    };
    
    fetchFtView();
  }, [imageState.hasImage, imageState.src, ftView, id]);

  const handleDoubleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      loadImage(id, file);
      // Reset input to allow re-uploading the same file or different file
      e.target.value = '';
    }
  };

  // Brightness/Contrast handlers for Original view
  const handleMouseDownOriginal = (e) => {
    if (!imageState.hasImage) return;
    // Single click to start dragging for brightness/contrast
    setIsDraggingOriginal(true);
    dragStartOriginal.current = { 
      x: e.clientX, 
      y: e.clientY,
      initialB: imageState.brightness,
      initialC: imageState.contrast
    };
  };

  const handleMouseMoveOriginal = (e) => {
    if (!isDraggingOriginal) return;
    // Calculate delta from start position
    const deltaX = e.clientX - dragStartOriginal.current.x;
    const deltaY = e.clientY - dragStartOriginal.current.y;
    // Calculate target values from initial + delta
    const targetBrightness = dragStartOriginal.current.initialB + (deltaX * 0.5);
    const targetContrast = dragStartOriginal.current.initialC + (-deltaY * 0.01);
    setBrightnessContrast(id, 'input', targetBrightness, targetContrast);
  };

  const handleMouseUpOriginal = () => {
    setIsDraggingOriginal(false);
  };

  // Brightness/Contrast handlers for FT view
  const handleMouseDownFt = (e) => {
    if (!imageState.hasImage) return;
    // Only handle brightness/contrast if in that mode
    if (ftInteractionMode === 'brightness') {
      setIsDraggingFt(true);
      dragStartFt.current = { 
        x: e.clientX, 
        y: e.clientY,
        initialB: imageState.ftBrightness,
        initialC: imageState.ftContrast
      };
    }
  };

  const handleMouseMoveFt = (e) => {
    if (!isDraggingFt) return;
    // Calculate delta from start position
    const deltaX = e.clientX - dragStartFt.current.x;
    const deltaY = e.clientY - dragStartFt.current.y;
    // Calculate target values from initial + delta
    const targetBrightness = dragStartFt.current.initialB + (deltaX * 0.5);
    const targetContrast = dragStartFt.current.initialC + (-deltaY * 0.01);
    setFtBrightnessContrast(id, targetBrightness, targetContrast);
  };

  const handleMouseUpFt = () => {
    setIsDraggingFt(false);
  };

  // Region overlay handlers (draggable and resizable)
  const mixerRegion = useAppStore(state => state.mixerSettings.region);
  const setUnifiedRegion = useAppStore(state => state.setUnifiedRegion);
  const setPerImageRegion = useAppStore(state => state.setPerImageRegion);
  
  const [isDraggingRegion, setIsDraggingRegion] = React.useState(false);
  const [isResizingRegion, setIsResizingRegion] = React.useState(false);
  const [resizeCorner, setResizeCorner] = React.useState(null);
  const regionDragStart = useRef({ x: 0, y: 0, startX: 0, startY: 0 });
  const resizeStartRef = useRef({ x: 0, y: 0, startX: 0, startY: 0, startWidth: 0, startHeight: 0 });

  // Get current region settings based on mode
  const currentRegion = mixerRegion.mode === 'unified' 
    ? mixerRegion.unified 
    : mixerRegion.perImage[id];

  // Update region helper
  const updateRegion = React.useCallback((key, value) => {
    if (mixerRegion.mode === 'unified') {
      setUnifiedRegion(key, value);
    } else {
      setPerImageRegion(id, key, value);
    }
  }, [mixerRegion.mode, id, setUnifiedRegion, setPerImageRegion]);

  // Region drag handlers
  const onRegionMouseDown = (e) => {
    if (!mixerRegion.enabled || ftInteractionMode !== 'region') return;
    e.stopPropagation();
    setIsDraggingRegion(true);
    regionDragStart.current = {
      x: e.clientX,
      y: e.clientY,
      startX: currentRegion.x,
      startY: currentRegion.y
    };
  };

  // Region resize handlers
  const onResizeMouseDown = (e, corner) => {
    if (!mixerRegion.enabled || ftInteractionMode !== 'region') return;
    e.stopPropagation();
    setIsResizingRegion(true);
    setResizeCorner(corner);
    resizeStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      startX: currentRegion.x,
      startY: currentRegion.y,
      startWidth: currentRegion.width,
      startHeight: currentRegion.height
    };
  };

  // Mouse move handler for dragging and resizing
  React.useEffect(() => {
    if (!isDraggingRegion && !isResizingRegion) return;

    const onMouseMove = (e) => {
      const rect = containerFtRef.current?.getBoundingClientRect();
      if (!rect) return;

      if (isDraggingRegion) {
        // Dragging - update position
        const deltaX = (e.clientX - regionDragStart.current.x) / rect.width;
        const deltaY = (e.clientY - regionDragStart.current.y) / rect.height;
        const newX = Math.max(0, Math.min(1, regionDragStart.current.startX + deltaX));
        const newY = Math.max(0, Math.min(1, regionDragStart.current.startY + deltaY));
        updateRegion('x', newX);
        updateRegion('y', newY);
      } else if (isResizingRegion) {
        // Resizing - update width/height based on corner
        const deltaX = (e.clientX - resizeStartRef.current.x) / rect.width;
        const deltaY = (e.clientY - resizeStartRef.current.y) / rect.height;
        
        let newWidth = resizeStartRef.current.startWidth;
        let newHeight = resizeStartRef.current.startHeight;
        let newX = resizeStartRef.current.startX;
        let newY = resizeStartRef.current.startY;

        // Adjust based on which corner is being dragged
        if (resizeCorner.includes('e')) { // East (right)
          newWidth = Math.max(0.05, Math.min(1, resizeStartRef.current.startWidth + deltaX * 2));
        }
        if (resizeCorner.includes('w')) { // West (left)
          newWidth = Math.max(0.05, Math.min(1, resizeStartRef.current.startWidth - deltaX * 2));
          newX = resizeStartRef.current.startX + deltaX;
        }
        if (resizeCorner.includes('s')) { // South (bottom)
          newHeight = Math.max(0.05, Math.min(1, resizeStartRef.current.startHeight + deltaY * 2));
        }
        if (resizeCorner.includes('n')) { // North (top)
          newHeight = Math.max(0.05, Math.min(1, resizeStartRef.current.startHeight - deltaY * 2));
          newY = resizeStartRef.current.startY + deltaY;
        }

        updateRegion('width', newWidth);
        updateRegion('height', newHeight);
        updateRegion('x', Math.max(0, Math.min(1, newX)));
        updateRegion('y', Math.max(0, Math.min(1, newY)));
      }
    };

    const onMouseUp = () => {
      setIsDraggingRegion(false);
      setIsResizingRegion(false);
      setResizeCorner(null);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [isDraggingRegion, isResizingRegion, resizeCorner, currentRegion, mixerRegion.mode, updateRegion]);

  // Track container dimensions for overlay calculations
  const [containerDimensions, setContainerDimensions] = React.useState({ width: 0, height: 0 });

  React.useEffect(() => {
    const updateDimensions = () => {
      const rect = containerFtRef.current?.getBoundingClientRect();
      if (rect) {
        setContainerDimensions({ width: rect.width, height: rect.height });
      }
    };
    
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, [ftSrc]);

  // Compute rectangle position/size for overlay
  const rectInfo = React.useMemo(() => {
    if (!containerDimensions.width || !containerDimensions.height) return null;
    
    const regionWidth = currentRegion.width * containerDimensions.width;
    const regionHeight = currentRegion.height * containerDimensions.height;
    const left = currentRegion.x * containerDimensions.width - regionWidth / 2;
    const top = currentRegion.y * containerDimensions.height - regionHeight / 2;
    
    return { 
      left, 
      top, 
      width: regionWidth, 
      height: regionHeight,
      containerWidth: containerDimensions.width,
      containerHeight: containerDimensions.height
    };
  }, [currentRegion.x, currentRegion.y, currentRegion.width, currentRegion.height, containerDimensions]);

  return (
    <div className="flex flex-col h-full panel-bg panel-border">
      {/* Header */}
      <div className="flex items-center justify-between px-2 py-1 border-b border-border bg-surface-lighter">
        <h3 className="font-semibold text-xs italic">{title}</h3>
        {imageState.hasImage && (
          <button
            onClick={() => clearImage(id)}
            className="p-1 hover:bg-surface rounded transition-colors text-text-muted hover:text-red-500"
            title="Remove image"
          >
            <X size={14} />
          </button>
        )}
      </div>

      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        accept="image/png, image/jpeg, image/jpg, image/webp"
        onChange={handleFileChange}
      />

      {/* Two Canvas Areas Stacked Vertically */}
      <div className="flex flex-row flex-1 min-h-0">
        {/* Original/Grayscale View */}
        <div className="flex-1 flex flex-col border-b border-border">
          <div className="flex items-center justify-between px-1.5 py-0.5 bg-surface border-b border-border">
            <span className="text-xs text-text-muted font-medium">Original</span>
            <select
              className="bg-background border border-border rounded text-xs px-1 py-0.5 focus:border-primary outline-none"
              value={originalView}
              onChange={(e) => setOriginalView(e.target.value)}
              disabled={!imageState.hasImage}
            >
              {ORIGINAL_OPTIONS.map(opt => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>
          <div 
            className="flex-1 min-h-0 relative bg-background overflow-hidden cursor-crosshair group"
            onDoubleClick={handleDoubleClick}
            onMouseDown={handleMouseDownOriginal}
            onMouseMove={handleMouseMoveOriginal}
            onMouseUp={handleMouseUpOriginal}
            onMouseLeave={handleMouseUpOriginal}
          >
            {imageState.isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            )}
            
            {!imageState.hasImage ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-text-muted transition-colors group-hover:text-text">
                <Upload size={32} className="mb-2 opacity-50" />
                <p className="text-xs font-medium">Double-click to upload</p>
              </div>
            ) : (
              <img
                src={originalSrc}
                alt={`${title} original`}
                className="w-full h-full object-contain pointer-events-none select-none"
                style={{ filter: `brightness(${100 + imageState.brightness}%) contrast(${imageState.contrast})` }}
              />
            )}
            
            {/* Brightness/Contrast indicator for Original view */}
            {isDraggingOriginal && (
              <div className="absolute bottom-2 left-2 bg-black/80 text-xs px-2 py-1 rounded text-white pointer-events-none z-20 shadow-lg backdrop-blur-sm">
                <div className="font-semibold">Original</div>
                <div className="flex items-center space-x-2 mt-1">
                  <span>B: {Math.round(imageState.brightness)}</span>
                  <span>C: {imageState.contrast.toFixed(2)}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* FT Component View */}
        <div className="flex-1 flex flex-col">
          <div className="flex items-center justify-between px-1.5 py-0.5 bg-surface border-b border-border">
            <span className="text-xs text-text-muted font-medium">FT Component</span>
            <select
              className="bg-background border border-border rounded text-xs px-1 py-0.5 focus:border-primary outline-none"
              value={ftView}
              onChange={(e) => setFtView(e.target.value)}
              disabled={!imageState.hasImage}
            >
              {FT_COMPONENT_OPTIONS.map(opt => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>
          <div 
            ref={containerFtRef}
            className={`flex-1 min-h-0 relative bg-background overflow-hidden ${ftInteractionMode === 'brightness' ? 'cursor-crosshair' : ''}`}
            onMouseDown={ftInteractionMode === 'brightness' ? handleMouseDownFt : undefined}
            onMouseMove={ftInteractionMode === 'brightness' ? handleMouseMoveFt : undefined}
            onMouseUp={ftInteractionMode === 'brightness' ? handleMouseUpFt : undefined}
            onMouseLeave={ftInteractionMode === 'brightness' ? handleMouseUpFt : undefined}
          >
            {!imageState.hasImage ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-text-muted">
                <ImageIcon size={32} className="mb-2 opacity-50"/>
                <p className="text-xs font-medium">Waiting for image...</p>
              </div>
            ) : (
              <img
                src={ftSrc}
                alt={`${title} FT`}
                className="w-full h-full object-contain pointer-events-none select-none"
                style={{ filter: `brightness(${100 + imageState.ftBrightness}%) contrast(${imageState.ftContrast})` }}
              />
            )}

            {/* Mode Toggle Buttons (only when region is enabled) */}
            {mixerRegion.enabled && imageState.hasImage && (
              <div className="absolute left-2 top-2 bg-background/90 border border-border rounded p-1 text-xs flex items-center space-x-1 z-20">
                <button
                  className={`px-2 py-1 rounded transition-colors ${ftInteractionMode === 'region' ? 'bg-primary text-white' : 'text-text-muted hover:bg-surface'}`}
                  onClick={() => setFtInteractionMode('region')}
                  title="Region Control Mode"
                >
                  Region
                </button>
                <button
                  className={`px-2 py-1 rounded transition-colors ${ftInteractionMode === 'brightness' ? 'bg-primary text-white' : 'text-text-muted hover:bg-surface'}`}
                  onClick={() => setFtInteractionMode('brightness')}
                  title="Brightness/Contrast Mode"
                >
                  B/C
                </button>
              </div>
            )}

            {/* Brightness/Contrast indicator for FT view */}
            {isDraggingFt && (
              <div className="absolute bottom-2 left-2 bg-black/80 text-xs px-2 py-1 rounded text-white pointer-events-none z-20 shadow-lg backdrop-blur-sm">
                <div className="font-semibold">FT Component</div>
                <div className="flex items-center space-x-2 mt-1">
                  <span>B: {Math.round(imageState.ftBrightness)}</span>
                  <span>C: {imageState.ftContrast.toFixed(2)}</span>
                </div>
              </div>
            )}

            {/* Region Overlay (draggable and resizable) */}
            {mixerRegion.enabled && rectInfo && ftInteractionMode === 'region' && (
              <div className="absolute inset-0 pointer-events-auto">
                {/* Outer overlay for 'outer' selection; inner rect highlighted for 'inner' */}
                {currentRegion[ftView.toLowerCase()] === 'outer' ? (
                  <>
                    <div className="absolute inset-0 bg-primary/20 pointer-events-none"></div>
                    <div
                      className="absolute border-2 border-primary rounded bg-transparent cursor-move"
                      style={{ 
                        left: `${rectInfo.left}px`, 
                        top: `${rectInfo.top}px`, 
                        width: `${rectInfo.width}px`, 
                        height: `${rectInfo.height}px` 
                      }}
                      onMouseDown={onRegionMouseDown}
                    >
                      {/* Corner resize handles */}
                      <div onMouseDown={(e) => onResizeMouseDown(e, 'nw')} className="absolute -left-1 -top-1 w-3 h-3 bg-primary rounded-full cursor-nwse-resize" />
                      <div onMouseDown={(e) => onResizeMouseDown(e, 'ne')} className="absolute -right-1 -top-1 w-3 h-3 bg-primary rounded-full cursor-nesw-resize" />
                      <div onMouseDown={(e) => onResizeMouseDown(e, 'sw')} className="absolute -left-1 -bottom-1 w-3 h-3 bg-primary rounded-full cursor-nesw-resize" />
                      <div onMouseDown={(e) => onResizeMouseDown(e, 'se')} className="absolute -right-1 -bottom-1 w-3 h-3 bg-primary rounded-full cursor-nwse-resize" />
                    </div>
                  </>
                ) : (
                  <div
                    className="absolute bg-primary/25 border-2 border-primary rounded cursor-move"
                    style={{ 
                      left: `${rectInfo.left}px`, 
                      top: `${rectInfo.top}px`, 
                      width: `${rectInfo.width}px`, 
                      height: `${rectInfo.height}px` 
                    }}
                    onMouseDown={onRegionMouseDown}
                  >
                    {/* Corner resize handles */}
                    <div onMouseDown={(e) => onResizeMouseDown(e, 'nw')} className="absolute -left-1 -top-1 w-3 h-3 bg-primary rounded-full cursor-nwse-resize z-10" />
                    <div onMouseDown={(e) => onResizeMouseDown(e, 'ne')} className="absolute -right-1 -top-1 w-3 h-3 bg-primary rounded-full cursor-nesw-resize z-10" />
                    <div onMouseDown={(e) => onResizeMouseDown(e, 'sw')} className="absolute -left-1 -bottom-1 w-3 h-3 bg-primary rounded-full cursor-nesw-resize z-10" />
                    <div onMouseDown={(e) => onResizeMouseDown(e, 'se')} className="absolute -right-1 -bottom-1 w-3 h-3 bg-primary rounded-full cursor-nwse-resize z-10" />
                  </div>
                )}

                {/* Control to toggle inner/outer for current FT component */}
                {mixerRegion.mode === 'independent' && (
                  <div className="absolute right-2 top-2 bg-background/90 border border-border rounded p-1 text-xs flex items-center space-x-1 z-20">
                    <span className="text-text-muted px-1">{ftView}:</span>
                    <button
                      className={`px-2 py-0.5 rounded ${currentRegion[ftView.toLowerCase()] === 'inner' ? 'bg-primary text-white' : 'text-text-muted hover:bg-surface'}`}
                      onClick={() => updateRegion(ftView.toLowerCase(), 'inner')}
                    >Inner</button>
                    <button
                      className={`px-2 py-0.5 rounded ${currentRegion[ftView.toLowerCase()] === 'outer' ? 'bg-primary text-white' : 'text-text-muted hover:bg-surface'}`}
                      onClick={() => updateRegion(ftView.toLowerCase(), 'outer')}
                    >Outer</button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImagePairViewer;
