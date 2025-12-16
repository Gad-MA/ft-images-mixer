import { create } from 'zustand';
import { api } from '../utils/api'; 

// ... (Keep createInitialImageState same as before) ...
const createInitialImageState = (id, type) => ({
  id,
  type, 
  hasImage: false,
  src: null, 
  componentType: type === 'input' ? 'Original' : 'Magnitude',
  brightness: 0,
  contrast: 1.0,
  isLoading: false,
});

export const useAppStore = create((set, get) => ({
  // ... (Keep initial state same as before) ...
  inputImages: Array.from({ length: 4 }, (_, i) => createInitialImageState(i, 'input')),
  outputImages: Array.from({ length: 2 }, (_, i) => createInitialImageState(i, 'output')),

  mixerSettings: {
    mode: 'magnitude_phase',
    targetOutputPort: 0,
    weights: {
      magnitude: [0.5, 0.5, 0.5, 0.5],
      phase: [0.5, 0.5, 0.5, 0.5],
      real: [0.5, 0.5, 0.5, 0.5],
      imaginary: [0.5, 0.5, 0.5, 0.5],
    },
    region: { enabled: false, type: 'inner', size: 0.3 }
  },

  processingStatus: { isProcessing: false, progress: 0 },
  lastMixTime: 0, // Timestamp of last successful mix

  // --- ACTIONS ---

  loadImage: async (slotId, file) => {
    set(state => {
        const newInputs = [...state.inputImages];
        newInputs[slotId].isLoading = true;
        return { inputImages: newInputs };
    });

    try {
        // REAL API CALL
        const result = await api.uploadImage(slotId, file);
        
        if (result.success) {
            set(state => {
              const newInputs = [...state.inputImages];
              newInputs[slotId] = {
                  ...newInputs[slotId],
                  hasImage: true,
                  src: result.imageUrl,
                  isLoading: false,
              };
              return { inputImages: newInputs };
            });
            // Update other images (sizes might have changed due to "One Size" rule)
            get().refreshAllViews(); 
            get().triggerMixing();
        }
    } catch (err) {
        console.error("Upload failed", err);
        set(state => {
             const newInputs = [...state.inputImages];
             newInputs[slotId].isLoading = false;
             return { inputImages: newInputs };
        });
    }
  },

  setComponentType: async (slotId, type, component) => {
    // Update component type
    set(state => {
      const targetArray = type === 'input' ? 'inputImages' : 'outputImages';
      const newImages = [...state[targetArray]];
      newImages[slotId] = {
        ...newImages[slotId],
        componentType: component
      };
      return { [targetArray]: newImages };
    });
    // Fetch the new component view
    await get().fetchImageView(slotId, type);
  },

    setBrightnessContrast: (slotId, type, bValue, cValue) => {
        set(state => {
            const targetArray = type === 'input' ? 'inputImages' : 'outputImages';
            const newImages = [...state[targetArray]];
            
            // Clamp values to valid CSS ranges
            // Brightness: -100 to 100 (Where 0 is default)
            const newB = Math.max(-100, Math.min(100, bValue));
            // Contrast: 0 to 5 (Where 1 is default)
            const newC = Math.max(0, Math.min(5.0, cValue));

            newImages[slotId].brightness = newB;
            newImages[slotId].contrast = newC;
            return { [targetArray]: newImages };
        });
        // DO NOT call fetchImageView here. 
        // We handle B/C strictly in CSS for performance and data integrity.
    },

    fetchImageView: async (slotId, type) => {
        const imgState = get()[type === 'input' ? 'inputImages' : 'outputImages'][slotId];
        if (!imgState.hasImage && type === 'input') return;

        try {
            // Map component names to API expected values
            // Original -> color, Greyscale -> grayscale, others lowercase
            let apiComponent = imgState.componentType.toLowerCase();
            if (imgState.componentType === 'Original') {
                apiComponent = 'color';
            } else if (imgState.componentType === 'Greyscale') {
                apiComponent = 'grayscale';
            }
            
            // Request RAW data only - brightness/contrast applied in CSS
            const result = await api.getView(
                slotId, 
                type, 
                apiComponent
            );

            if (!result.success) {
                console.error(`Failed to fetch ${type} view:`, result.error);
                return;
            }

            if (result.success) {
                set(state => {
                    const targetArray = type === 'input' ? 'inputImages' : 'outputImages';
                    const newImages = [...state[targetArray]];
                    newImages[slotId].src = result.imageUrl;
                    if(type === 'output') newImages[slotId].hasImage = true;
                    return { [targetArray]: newImages };
                });
            }
        } catch (err) {
            console.error("View fetch error", err);
        }
    },

  refreshAllViews: () => {
      // Helper to refresh all valid images (useful after resize)
      const { inputImages } = get();
      inputImages.forEach(img => {
          if (img.hasImage) get().fetchImageView(img.id, 'input');
      });
  },

  // --- MIXER ACTIONS ---
  
  setMixerMode: (mode) => {
    set(state => ({ mixerSettings: { ...state.mixerSettings, mode } }));
    get().triggerMixing();
  },
  
  setTargetOutput: (portId) => {
     set(state => ({ mixerSettings: { ...state.mixerSettings, targetOutputPort: portId } }));
  },
  
  setWeight: (component, index, value) => {
    set(state => {
      const newWeights = { ...state.mixerSettings.weights };
      newWeights[component] = [...newWeights[component]];
      newWeights[component][index] = value;
      return { mixerSettings: { ...state.mixerSettings, weights: newWeights } };
    });
    get().triggerMixing();
  },
  
  setRegionSetting: (key, value) => {
      set(state => ({
          mixerSettings: {
              ...state.mixerSettings,
              region: { ...state.mixerSettings.region, [key]: value }
          }
      }));
      get().triggerMixing();
  },

  triggerMixing: async () => {
      const { mixerSettings, processingStatus } = get();
      
      // Cancel if already running
      if (processingStatus.isProcessing) {
          return; // Just ignore if already processing
      }

      // Simulate progress in frontend
      set({ processingStatus: { isProcessing: true, progress: 0 } });

      // Animate progress
      let progress = 0;
      const progressInterval = setInterval(() => {
          progress += 10;
          if (progress <= 90) {
              set({ processingStatus: { isProcessing: true, progress } });
          }
      }, 50); // Update every 50ms

      // Map frontend state names to backend expected names
      // Include only the slots that have images loaded
      const activeSlots = get().inputImages
          .filter(img => img.hasImage)
          .map(img => img.id);
      
      // ALWAYS send all 4 weight sets (magnitude, phase, real, imaginary)
      // Backend will use the appropriate ones based on mode
      const apiPayload = {
          mode: mixerSettings.mode,
          weights: {
              magnitude: mixerSettings.weights.magnitude,
              phase: mixerSettings.weights.phase,
              real: mixerSettings.weights.real,
              imaginary: mixerSettings.weights.imaginary
          },
          region: mixerSettings.region,
          output_port: mixerSettings.targetOutputPort,
          active_slots: activeSlots // Tell backend which images to use
      };

      try {
          // Call mixing API (no polling needed)
          await api.startMixing(apiPayload);
          
          // Clear progress animation
          clearInterval(progressInterval);
          
          // Set to complete
          set({ processingStatus: { isProcessing: false, progress: 100 }, lastMixTime: Date.now() });
          
          // Fetch the result ONCE
          await get().fetchImageView(mixerSettings.targetOutputPort, 'output');
          
          // Reset progress after a short delay
          setTimeout(() => {
              set({ processingStatus: { isProcessing: false, progress: 0 } });
          }, 500);

      } catch (err) {
          console.error("Mixing failed", err);
          clearInterval(progressInterval);
          set({ processingStatus: { isProcessing: false, progress: 0 } });
      }
    },
    resetWeights: () => {
        set(state => ({
            mixerSettings: {
                ...state.mixerSettings,
                weights: {
                    magnitude: [0.5, 0.5, 0.5, 0.5],
                    phase: [0.5, 0.5, 0.5, 0.5],
                    real: [0.5, 0.5, 0.5, 0.5],
                    imaginary: [0.5, 0.5, 0.5, 0.5],
                }
            }
        }));
        get().triggerMixing();
    },
}));