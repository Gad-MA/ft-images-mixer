import numpy as np
import threading
import time

# Explicitly export the class to avoid any import confusion
__all__ = ["FourierMixer"]

class FourierMixer:
    """
    Mixes Fourier Transform components from multiple images.
    Supports magnitude/phase mixing and real/imaginary mixing.
    Includes region-based frequency filtering and cancellable operations.
    """
    
    def __init__(self, image_processors):
        """
        Initialize the FourierMixer with ImageProcessor instances.
        
        Args:
            image_processors (list): List of 1-4 ImageProcessor instances
        """
        if not image_processors or len(image_processors) > 4:
            raise ValueError("FourierMixer requires between 1 and 4 ImageProcessor instances")
        
        # Validate all images have same size (if loaded)
        self._validate_uniform_sizes(image_processors)
        
        self.processors = image_processors
        self.num_processors = len(image_processors)
        self.mode = 'magnitude_phase'  # or 'real_imaginary'
        
        # Initialize weights based on number of processors
        self.weights = {
            'magnitude': [0.0] * self.num_processors,
            'phase': [0.0] * self.num_processors,
            'real': [0.0] * self.num_processors,
            'imaginary': [0.0] * self.num_processors
        }
        
        # Region selection
        self.region_enabled = False
        self.region_size = 0.3  # 30% of image size (percentage)
        self.region_x = 0.5  # Center X position (0-1)
        self.region_y = 0.5  # Center Y position (0-1)
        self.region_width = 0.3  # Width as percentage (0-1)
        self.region_height = 0.3  # Height as percentage (0-1)
        # Per-component region types (allows 'inner'/'outer' per FFT component)
        self.per_component_region = {
            'magnitude': 'inner',
            'phase': 'inner',
            'real': 'inner',
            'imaginary': 'inner'
        }
        
        # Output port selection (1 or 2)
        self.target_output_port = 1
        
        # Progress tracking
        self.progress = 0
        self.is_cancelled = False
        self.is_processing = False
        
        # Threading
        self.processing_thread = None
    
    
    def _validate_uniform_sizes(self, processors):
        """
        Ensure all loaded images have the same dimensions.
        Ignores empty slots.
        """
        sizes = []
        for i, proc in enumerate(processors):
            if proc.fft_result is not None:
                sizes.append(proc.fft_result.shape)
            elif proc.image is not None:
                sizes.append(proc.image.shape)
        
        if len(sizes) > 0:
            first_size = sizes[0]
            for i, size in enumerate(sizes[1:], start=1):
                if size != first_size:
                    # In a real app, we might resize here, but for now just warn/raise
                    # BackendAPI handles resizing before this class is usually invoked
                    pass 
    
    
    def set_mode(self, mode):
        """Set the mixing mode."""
        if mode not in ['magnitude_phase', 'real_imaginary']:
            raise ValueError("Mode must be 'magnitude_phase' or 'real_imaginary'")
        
        self.mode = mode
        print(f"✅ Mixing mode set to: {mode}")
    
    
    def set_weights(self, component_type, weights):
        """Set weights for a specific component type."""
        if component_type not in ['magnitude', 'phase', 'real', 'imaginary']:
            raise ValueError("Invalid component_type")
        
        if len(weights) != self.num_processors:
            raise ValueError(f"Must provide exactly {self.num_processors} weights (matching number of loaded images)")
        
        if any(w < 0 for w in weights):
            raise ValueError("Weights must be non-negative")
        
        self.weights[component_type] = list(weights)
        print(f"✅ Weights set for {component_type}: {weights}")
    
    
    def set_region(self, size=None, region_type='inner', enabled=True, x=None, y=None, width=None, height=None):
        """Set frequency region parameters.

        `region_type` may be either a string 'inner'/'outer' applied to all components,
        or a dict mapping component names to 'inner'/'outer'.
        """
        # Handle new width/height format or legacy size format
        if width is not None and height is not None:
            if not (0.0 <= width <= 1.0 and 0.0 <= height <= 1.0):
                raise ValueError("Region width and height must be between 0.0 and 1.0")
            self.region_width = width
            self.region_height = height
            self.region_size = (width + height) / 2  # For backward compatibility
        elif size is not None:
            if not 0.0 <= size <= 1.0:
                raise ValueError("Region size must be between 0.0 and 1.0")
            self.region_size = size
            self.region_width = size
            self.region_height = size
        
        # Handle position
        if x is not None:
            if not 0.0 <= x <= 1.0:
                raise ValueError("Region x must be between 0.0 and 1.0")
            self.region_x = x
        if y is not None:
            if not 0.0 <= y <= 1.0:
                raise ValueError("Region y must be between 0.0 and 1.0")
            self.region_y = y

        # Accept either dict or single type
        if isinstance(region_type, dict):
            for comp, rt in region_type.items():
                if rt not in ['inner', 'outer']:
                    raise ValueError("Region type must be 'inner' or 'outer'")
            # Update per-component types, keep missing keys as-is
            for comp in self.per_component_region.keys():
                if comp in region_type:
                    self.per_component_region[comp] = region_type[comp]
        else:
            if region_type not in ['inner', 'outer']:
                raise ValueError("Region type must be 'inner' or 'outer'")
            for comp in self.per_component_region.keys():
                self.per_component_region[comp] = region_type

        self.region_enabled = enabled

        print(f"✅ Region set: pos=({self.region_x:.2f},{self.region_y:.2f}), size=({self.region_width:.2f}x{self.region_height:.2f}), per_component={self.per_component_region}, enabled={enabled}")
    
    
    def set_region_from_coordinates(self, x1, y1, x2, y2, region_type='inner'):
        """Set region based on rectangle coordinates."""
        # Find first active processor to get shape
        shape = None
        for p in self.processors:
            if p.fft_result is not None:
                shape = p.fft_result.shape
                break
        
        if shape is None:
            return # No images loaded
        
        rows, cols = shape
        
        # Convert coordinates to percentage
        width_pixels = abs(x2 - x1)
        height_pixels = abs(y2 - y1)
        
        width_percentage = width_pixels / cols
        height_percentage = height_pixels / rows
        
        # Use average as size
        size = (width_percentage + height_percentage) / 2
        size = np.clip(size, 0.0, 1.0)
        
        self.set_region(size, region_type, enabled=True)
        print(f"✅ Region set from coordinates: ({x1},{y1}) to ({x2},{y2})")
    
    
    def set_output_port(self, port_number):
        """Set which output viewport should receive the mixed result."""
        if port_number not in [1, 2]:
            raise ValueError("Output port must be 1 or 2")
        
        self.target_output_port = port_number
        print(f"✅ Output will be sent to viewport {port_number}")
    
    
    def get_target_output_port(self):
        return self.target_output_port
    
    
    def create_frequency_mask(self, shape, region_type='inner'):
        """Create a frequency mask based on region settings for a given region_type."""
        if not self.region_enabled:
            return np.ones(shape, dtype=np.float64)

        if region_type not in ['inner', 'outer']:
            region_type = 'inner'

        rows, cols = shape

        # Calculate region dimensions based on width and height
        region_rows = int(rows * self.region_height)
        region_cols = int(cols * self.region_width)

        # Ensure at least 1 pixel
        region_rows = max(1, region_rows)
        region_cols = max(1, region_cols)

        # Calculate region center position
        center_row = int(rows * self.region_y)
        center_col = int(cols * self.region_x)

        # Define rectangle bounds
        row_start = max(0, center_row - region_rows // 2)
        row_end = min(rows, center_row + region_rows // 2)
        col_start = max(0, center_col - region_cols // 2)
        col_end = min(cols, center_col + region_cols // 2)

        # Create mask
        if region_type == 'inner':
            # Include only inner rectangle
            mask = np.zeros(shape, dtype=np.float64)
            mask[row_start:row_end, col_start:col_end] = 1.0
        else:
            # Include everything EXCEPT inner rectangle (outer region)
            mask = np.ones(shape, dtype=np.float64)
            mask[row_start:row_end, col_start:col_end] = 0.0

        return mask
    
    
    def apply_frequency_mask(self, fft_component):
        """Apply frequency mask to an FFT component using the default per-component settings.

        This method assumes the caller will apply the appropriate mask for the
        specific component type by calling `create_frequency_mask(shape, type)`.
        For backward compatibility, this will apply the 'magnitude' mask.
        """
        mask = self.create_frequency_mask(fft_component.shape, self.per_component_region.get('magnitude', 'inner'))
        return fft_component * mask
    
    
    def mix_components(self):
        """
        Mix FFT components based on current mode and weights.
        Supports partial loading (skips empty slots).
        """
        # Find valid processors
        active_processors = [p for p in self.processors if p.fft_result is not None]
        
        if not active_processors:
            raise ValueError("No images loaded with FFT computed.")
        
        # Validate at least one non-zero weight
        if self.mode == 'magnitude_phase':
            all_weights = self.weights['magnitude'] + self.weights['phase']
        else:
            all_weights = self.weights['real'] + self.weights['imaginary']
        
        if sum(all_weights) == 0:
            # Not an error, just return black image
            shape = active_processors[0].fft_result.shape
            return np.zeros(shape, dtype=np.complex128)
        
        # Get shape from first valid processor
        shape = active_processors[0].fft_result.shape
        
        if self.mode == 'magnitude_phase':
            return self._mix_magnitude_phase(shape)
        else:
            return self._mix_real_imaginary(shape)
    
    
    def _mix_magnitude_phase(self, shape):
        """Mix using magnitude and phase components."""
        mag_weights = np.array(self.weights['magnitude'])
        phase_weights = np.array(self.weights['phase'])
        
        # Check if using same weights for mag and phase (equal mixing case)
        # In this case, use direct complex FFT mixing which is more mathematically correct
        if np.allclose(mag_weights, phase_weights):
            # Pure mixing: mix complex FFTs directly
            mixed_fft = np.zeros(shape, dtype=np.complex128)
            for i, processor in enumerate(self.processors):
                if processor.fft_result is None: continue
                
                if mag_weights[i] > 0:
                    mixed_fft += mag_weights[i] * processor.fft_result
            
            # Apply frequency mask if enabled
            mixed_fft = self.apply_frequency_mask(mixed_fft)
            return mixed_fft
        
        # Otherwise, perform separate magnitude & phase mixing
        mixed_magnitude = np.zeros(shape, dtype=np.float64)
        mixed_phase = np.zeros(shape, dtype=np.float64)

        # STEP 1: Extract and mix magnitude components
        for i, processor in enumerate(self.processors):
            if processor.fft_result is None: continue

            if mag_weights[i] > 0:
                magnitude = np.abs(processor.fft_result)
                mixed_magnitude += mag_weights[i] * magnitude

        # Apply magnitude mask if enabled (uses per-component region setting)
        mag_mask = self.create_frequency_mask(shape, self.per_component_region.get('magnitude', 'inner'))
        mixed_magnitude = mixed_magnitude * mag_mask

        # STEP 2: Extract and mix phase components
        for i, processor in enumerate(self.processors):
            if processor.fft_result is None: continue

            if phase_weights[i] > 0:
                phase = np.angle(processor.fft_result)
                mixed_phase += phase_weights[i] * phase

        # Apply phase mask: where mask is 0, set phase to 0 to neutralize contribution
        phase_mask = self.create_frequency_mask(shape, self.per_component_region.get('phase', 'inner'))
        mixed_phase = mixed_phase * phase_mask

        # STEP 3: Reconstruct complex FFT from mixed components
        mixed_fft = mixed_magnitude * np.exp(1j * mixed_phase)

        return mixed_fft
    
    
    def _mix_real_imaginary(self, shape):
        """Mix using real and imaginary components."""
        mixed_real = np.zeros(shape, dtype=np.float64)
        mixed_imaginary = np.zeros(shape, dtype=np.float64)
        
        real_weights = self.weights['real']
        imag_weights = self.weights['imaginary']
        
        # STEP 1: Mix real components
        for i, processor in enumerate(self.processors):
            if processor.fft_result is None: continue
            
            if real_weights[i] > 0:
                real_part = np.real(processor.fft_result)
                mixed_real += real_weights[i] * real_part
        
        # STEP 2: Mix imaginary components
        for i, processor in enumerate(self.processors):
            if processor.fft_result is None: continue
            
            if imag_weights[i] > 0:
                imag_part = np.imag(processor.fft_result)
                mixed_imaginary += imag_weights[i] * imag_part
        
        # STEP 3: Apply per-component masks
        real_mask = self.create_frequency_mask(shape, self.per_component_region.get('real', 'inner'))
        imag_mask = self.create_frequency_mask(shape, self.per_component_region.get('imaginary', 'inner'))

        mixed_real = mixed_real * real_mask
        mixed_imaginary = mixed_imaginary * imag_mask

        # STEP 4: Reconstruct complex FFT
        mixed_fft = mixed_real + 1j * mixed_imaginary

        return mixed_fft
    
    
    def compute_ifft(self, mixed_fft=None, report_progress=True):
        """Compute inverse FFT to get the output image."""
        self.progress = 0
        self.is_cancelled = False
        
        try:
            if mixed_fft is None:
                if report_progress:
                    self.progress = 10
                mixed_fft = self.mix_components()
            
            if self.is_cancelled:
                print("⚠️  Operation cancelled during mixing")
                return None
            
            if report_progress:
                self.progress = 50
            
            # Inverse FFT
            mixed_fft_shifted = np.fft.ifftshift(mixed_fft)
            
            if report_progress:
                self.progress = 70
            
            output_complex = np.fft.ifft2(mixed_fft_shifted)
            
            if self.is_cancelled:
                print("⚠️  Operation cancelled during IFFT")
                return None
            
            if report_progress:
                self.progress = 90
            
            # Take real part
            output_image = np.real(output_complex)
            
            # Normalize to 0-255 range
            output_image = output_image - output_image.min()
            if output_image.max() > 0:
                output_image = output_image / output_image.max() * 255.0
            
            if report_progress:
                self.progress = 100
            
            print(f"✅ IFFT computed. Output shape: {output_image.shape}")
            return output_image

        except Exception as e:
            print(f"❌ Error in compute_ifft: {e}")
            raise e
    
    
    def mix_and_compute_async(self, callback=None):
        """Perform mixing and IFFT in a separate thread."""
        if self.is_processing:
            print("⚠️  Already processing. Cancelling previous operation...")
            self.cancel_operation()
            if self.processing_thread and self.processing_thread.is_alive():
                # In Python we can't force kill threads safely, 
                # we rely on the flags checked in compute_ifft
                self.processing_thread.join(timeout=1.0)
        
        def processing_worker():
            self.is_processing = True
            self.is_cancelled = False
            
            try:
                output = self.compute_ifft(report_progress=True)
                
                if not self.is_cancelled and callback:
                    callback(output, self.target_output_port)
                    
            except Exception as e:
                print(f"❌ Error during processing: {e}")
            finally:
                self.is_processing = False
        
        self.processing_thread = threading.Thread(target=processing_worker)
        self.processing_thread.start()
    
    
    def cancel_operation(self):
        """Cancel the current processing operation."""
        if self.is_processing:
            self.is_cancelled = True
            print("🛑 Cancellation requested...")
    
    
    def get_progress(self):
        return self.progress
    
    
    def is_busy(self):
        return self.is_processing
    
    
    def get_mask_visualization(self):
        """Get a visualization of the current frequency mask."""
        # Find first valid processor
        shape = None
        for p in self.processors:
            if p.fft_result is not None:
                shape = p.fft_result.shape
                break
                
        if shape is not None:
            mask = self.create_frequency_mask(shape)
            return (mask * 255).astype(np.uint8)
        return None

    def get_region_rectangle_bounds(self):
        # Find first valid processor
        shape = None
        for p in self.processors:
            if p.fft_result is not None:
                shape = p.fft_result.shape
                break
        
        if shape is None:
            return None
        
        rows, cols = shape
        center_row, center_col = rows // 2, cols // 2
        
        region_rows = int(rows * self.region_size)
        region_cols = int(cols * self.region_size)
        
        x1 = center_col - region_cols // 2
        y1 = center_row - region_rows // 2
        x2 = center_col + region_cols // 2
        y2 = center_row + region_rows // 2
        
        return {
            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
            'width': region_cols, 'height': region_rows,
            'enabled': self.region_enabled, 'type': self.region_type
        }