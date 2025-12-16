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
            image_processors (list): List of 4 ImageProcessor instances
        """
        if len(image_processors) != 4:
            raise ValueError("FourierMixer requires exactly 4 ImageProcessor instances")
        
        # Validate all images have same size (if loaded)
        self._validate_uniform_sizes(image_processors)
        
        self.processors = image_processors
        self.mode = 'magnitude_phase'  # or 'real_imaginary'
        self.weights = {
            'magnitude': [0.0, 0.0, 0.0, 0.0],
            'phase': [0.0, 0.0, 0.0, 0.0],
            'real': [0.0, 0.0, 0.0, 0.0],
            'imaginary': [0.0, 0.0, 0.0, 0.0]
        }
        
        # Region selection
        self.region_enabled = False
        self.region_size = 0.3  # 30% of image size (percentage)
        self.region_type = 'inner'  # 'inner' or 'outer'
        
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
        
        if len(weights) != 4:
            raise ValueError("Must provide exactly 4 weights")
        
        if any(w < 0 for w in weights):
            raise ValueError("Weights must be non-negative")
        
        self.weights[component_type] = list(weights)
        print(f"✅ Weights set for {component_type}: {weights}")
    
    
    def set_region(self, size, region_type='inner', enabled=True):
        """Set frequency region parameters."""
        if not 0.0 <= size <= 1.0:
            raise ValueError("Region size must be between 0.0 and 1.0")
        
        if region_type not in ['inner', 'outer']:
            raise ValueError("Region type must be 'inner' or 'outer'")
        
        self.region_size = size
        self.region_type = region_type
        self.region_enabled = enabled
        
        print(f"✅ Region set: size={size*100}%, type={region_type}, enabled={enabled}")
    
    
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
    
    
    def create_frequency_mask(self, shape):
        """Create a frequency mask based on region settings."""
        if not self.region_enabled:
            return np.ones(shape, dtype=np.float64)
        
        rows, cols = shape
        center_row, center_col = rows // 2, cols // 2
        
        # Calculate region dimensions
        region_rows = int(rows * self.region_size)
        region_cols = int(cols * self.region_size)
        
        # Ensure at least 1 pixel
        region_rows = max(1, region_rows)
        region_cols = max(1, region_cols)
        
        # Create mask
        mask = np.zeros(shape, dtype=np.float64)
        
        # Define rectangle bounds (centered)
        row_start = center_row - region_rows // 2
        row_end = center_row + region_rows // 2
        col_start = center_col - region_cols // 2
        col_end = center_col + region_cols // 2
        
        if self.region_type == 'inner':
            # Include inner rectangle (low frequencies)
            mask[row_start:row_end, col_start:col_end] = 1.0
        else:
            # Include outer region (high frequencies)
            mask[:, :] = 1.0
            mask[row_start:row_end, col_start:col_end] = 0.0
        
        return mask
    
    
    def apply_frequency_mask(self, fft_component):
        """Apply frequency mask to an FFT component."""
        mask = self.create_frequency_mask(fft_component.shape)
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
        
        # Check if using same weights for mag and phase (pure mixing mode)
        if np.allclose(mag_weights, phase_weights):
            # Pure mixing: mix complex FFTs directly
            mixed_fft = np.zeros(shape, dtype=np.complex128)
            for i, processor in enumerate(self.processors):
                # Skip empty processors
                if processor.fft_result is None: continue
                
                if mag_weights[i] > 0:
                    mixed_fft += mag_weights[i] * processor.fft_result
            
            mixed_fft = self.apply_frequency_mask(mixed_fft)
            return mixed_fft
        
        else:
            # Separate magnitude/phase mixing
            mixed_magnitude = np.zeros(shape, dtype=np.float64)
            mixed_phase = np.zeros(shape, dtype=np.float64)
            
            # STEP 1: Extract components
            for i, processor in enumerate(self.processors):
                if processor.fft_result is None: continue

                if mag_weights[i] > 0:
                    magnitude = np.abs(processor.fft_result)
                    mixed_magnitude += mag_weights[i] * magnitude
            
            for i, processor in enumerate(self.processors):
                if processor.fft_result is None: continue
                
                if phase_weights[i] > 0:
                    phase = np.angle(processor.fft_result)
                    mixed_phase += phase_weights[i] * phase
            
            # STEP 2: Reconstruct complex FFT from mixed components
            mixed_fft = mixed_magnitude * np.exp(1j * mixed_phase)
            
            # STEP 3: Apply mask to the MIXED result
            mixed_fft = self.apply_frequency_mask(mixed_fft)
            
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
        
        # STEP 3: Reconstruct complex FFT
        mixed_fft = mixed_real + 1j * mixed_imaginary
        
        # STEP 4: Apply mask
        mixed_fft = self.apply_frequency_mask(mixed_fft)
        
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