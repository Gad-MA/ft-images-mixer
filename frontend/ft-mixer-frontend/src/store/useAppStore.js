import { create } from 'zustand';
import { api } from '../utils/api'; // IMPORT REAL API

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
    // Optimistic update
    set(state => {
      const targetArray = type === 'input' ? 'inputImages' : 'outputImages';
      const newImages = [...state[targetArray]];
      newImages[slotId].componentType = component;
      return { [targetArray]: newImages };
    });
    // Fetch real view
    get().fetchImageView(slotId, type);
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
            // ALWAYS Request RAW data (B=0, C=1.0)
            // This prevents the backend from destructively modifying the source image
            const result = await api.getView(
                slotId, 
                type, 
                imgState.componentType, 
                0,   // Always 0
                1.0  // Always 1.0
            );

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
          await api.cancelMixing();
      }

      set({ processingStatus: { isProcessing: true, progress: 0 } });

      // --- FIX STARTS HERE ---
      // Map frontend state names to backend expected names
      const apiPayload = {
          ...mixerSettings,
          output_port: mixerSettings.targetOutputPort // Backend expects 'output_port', not 'targetOutputPort'
      };
      // --- FIX ENDS HERE ---

      try {
          // Use apiPayload instead of mixerSettings
          await api.startMixing(apiPayload);

          // Start Polling Loop
          const pollInterval = setInterval(async () => {
              const status = await api.getProgress();
              
              set({ processingStatus: { 
                  isProcessing: status.is_processing, 
                  progress: status.progress 
              }});

              if (!status.is_processing) {
                  clearInterval(pollInterval);
                  // Fetch the final result for the target port
                  get().fetchImageView(mixerSettings.targetOutputPort, 'output');
              }
          }, 200); // Check every 200ms

      } catch (err) {
          console.error("Mixing failed", err);
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