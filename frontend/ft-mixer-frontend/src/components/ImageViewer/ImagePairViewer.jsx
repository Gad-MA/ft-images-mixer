import React, { useEffect, useRef } from 'react';
import { Upload, Image as ImageIcon } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { api } from '../../utils/api';

const ORIGINAL_OPTIONS = ['Original', 'Greyscale'];
const FT_COMPONENT_OPTIONS = ['Magnitude', 'Phase', 'Real', 'Imaginary'];

const ImagePairViewer = ({ id, title }) => {
  const imageState = useAppStore(state => state.inputImages[id]);
  const loadImage = useAppStore(state => state.loadImage);
  const setBrightnessContrast = useAppStore(state => state.setBrightnessContrast);
  
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
    const deltaX = e.clientX - dragStartOriginal.current.x;
    const deltaY = e.clientY - dragStartOriginal.current.y;
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
    setIsDraggingFt(true);
    dragStartFt.current = { 
      x: e.clientX, 
      y: e.clientY,
      initialB: imageState.brightness,
      initialC: imageState.contrast
    };
  };

  const handleMouseMoveFt = (e) => {
    if (!isDraggingFt) return;
    const deltaX = e.clientX - dragStartFt.current.x;
    const deltaY = e.clientY - dragStartFt.current.y;
    const targetBrightness = dragStartFt.current.initialB + (deltaX * 0.5);
    const targetContrast = dragStartFt.current.initialC + (-deltaY * 0.01);
    setBrightnessContrast(id, 'input', targetBrightness, targetContrast);
  };

  const handleMouseUpFt = () => {
    setIsDraggingFt(false);
  };

  // Region overlay and resize (unified across images)
  const mixerRegion = useAppStore(state => state.mixerSettings.region);
  const setRegionSetting = useAppStore(state => state.setRegionSetting);
  const setComponentRegionType = useAppStore(state => state.setComponentRegionType);
  const [isResizing, setIsResizing] = React.useState(false);
  const resizeStart = useRef({ x: 0, y: 0, startSize: 0 });

  // Resize handlers
  const onResizeMouseDown = (e) => {
    e.stopPropagation();
    setIsResizing(true);
    resizeStart.current = { x: e.clientX, y: e.clientY, startSize: mixerRegion.size };
  };

  React.useEffect(() => {
    if (!isResizing) return;
    const onMouseMove = (e) => {
      const rect = containerFtRef.current?.getBoundingClientRect();
      if (!rect) return;
      const minDim = Math.min(rect.width, rect.height);
      // Compute new size by comparing distance from center to pointer
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const dx = Math.abs(e.clientX - centerX);
      const dy = Math.abs(e.clientY - centerY);
      const newRectSize = Math.max(dx, dy) * 2; // diameter
      const newSize = Math.max(0.05, Math.min(0.95, newRectSize / minDim));
      setRegionSetting('size', newSize);
    };
    const onMouseUp = () => setIsResizing(false);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [isResizing, setRegionSetting, mixerRegion.size]);

  // Compute rectangle position/size for overlay based on current container
  const rectInfo = React.useMemo(() => {
    const rect = containerFtRef.current?.getBoundingClientRect();
    if (!rect) return null;
    const minDim = Math.min(rect.width, rect.height);
    const rectSize = Math.max(10, mixerRegion.size * minDim);
    const left = (rect.width - rectSize) / 2;
    const top = (rect.height - rectSize) / 2;
    return { left, top, rectSize, width: rect.width, height: rect.height };
  }, [mixerRegion.size, containerFtRef.current, ftSrc]);

  return (
    <div className="flex flex-col h-full panel-bg panel-border">
      {/* Header */}
      <div className="flex items-center justify-between px-2 py-1 border-b border-border bg-surface-lighter">
        <h3 className="font-semibold text-xs italic">{title}</h3>
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
            
            {isDraggingOriginal && (
              <div className="absolute bottom-2 left-2 bg-black/70 text-xs p-1 rounded text-text-muted pointer-events-none">
                B: {Math.round(imageState.brightness)}, C: {imageState.contrast.toFixed(2)}
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
            className="flex-1 min-h-0 relative bg-background overflow-hidden cursor-crosshair"
            onMouseDown={handleMouseDownFt}
            onMouseMove={handleMouseMoveFt}
            onMouseUp={handleMouseUpFt}
            onMouseLeave={handleMouseUpFt}
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
                style={{ filter: `brightness(${100 + imageState.brightness}%) contrast(${imageState.contrast})` }}
              />
            )}
            
            {isDraggingFt && (
              <div className="absolute bottom-2 left-2 bg-black/70 text-xs p-1 rounded text-text-muted pointer-events-none">
                B: {Math.round(imageState.brightness)}, C: {imageState.contrast.toFixed(2)}
              </div>
            )}

            {/* Region Overlay (unified) */}
            {mixerRegion.enabled && rectInfo && (
              <div className="absolute inset-0 pointer-events-auto">
                {/* Outer overlay for 'outer' selection; inner rect highlighted for 'inner' */}
                {mixerRegion[ftView.toLowerCase()] === 'outer' ? (
                  <>
                    <div className="absolute inset-0 bg-primary/20"></div>
                    <div
                      className="absolute border-2 border-primary rounded pointer-events-none"
                      style={{ left: rectInfo.left, top: rectInfo.top, width: rectInfo.rectSize, height: rectInfo.rectSize }}
                    />
                  </>
                ) : (
                  <div
                    className="absolute bg-primary/25 border-2 border-primary rounded pointer-events-none"
                    style={{ left: rectInfo.left, top: rectInfo.top, width: rectInfo.rectSize, height: rectInfo.rectSize }}
                  />
                )}

                {/* Resize handle */}
                <div
                  onMouseDown={onResizeMouseDown}
                  className="absolute w-4 h-4 bg-primary rounded-sm cursor-nwse-resize"
                  style={{ left: rectInfo.left + rectInfo.rectSize - 8, top: rectInfo.top + rectInfo.rectSize - 8 }}
                />

                {/* Small control to toggle inner/outer for current FT component */}
                <div className="absolute right-2 top-2 bg-background/90 border border-border rounded p-1 text-xs flex items-center space-x-1">
                  <button
                    className={`px-2 py-0.5 ${mixerRegion[ftView.toLowerCase()] === 'inner' ? 'bg-primary text-white' : 'text-text-muted'}`}
                    onClick={() => setComponentRegionType(ftView.toLowerCase(), 'inner')}
                  >Inner</button>
                  <button
                    className={`px-2 py-0.5 ${mixerRegion[ftView.toLowerCase()] === 'outer' ? 'bg-primary text-white' : 'text-text-muted'}`}
                    onClick={() => setComponentRegionType(ftView.toLowerCase(), 'outer')}
                  >Outer</button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImagePairViewer;
