import numpy as np
from classes.image_processor import ImageProcessor
from classes.component_visualizer import ComponentVisualizer
from classes.fourier_mixer import FourierMixer
import json
import base64
from io import BytesIO
from PIL import Image

# Explicitly export the class to avoid any import confusion
__all__ = ["BackendAPI"]


class BackendAPI:
    """
    Main API interface for the Fourier Mixer application.
    Handles all communication between frontend and backend classes.
    """
    
    def __init__(self):
        """Initialize the Backend API with 4 image processors."""
        self.image_processors = [ImageProcessor() for _ in range(4)]
        self.mixer = None
        self.output_images = [None, None]  # Two output ports
        
        # Store brightness/contrast settings for each component of each image
        # Format: {image_index: {component_type: {'brightness': float, 'contrast': float}}}
        self.component_display_settings = {}
        for i in range(4):
            self.component_display_settings[i] = {
                'magnitude': {'brightness': 0, 'contrast': 1.0},
                'phase': {'brightness': 0, 'contrast': 1.0},
                'real': {'brightness': 0, 'contrast': 1.0},
                'imaginary': {'brightness': 0, 'contrast': 1.0}
            }
        
        print("✅ BackendAPI initialized with 4 image slots")
    
    
    def load_image(self, image_index, image_path):
        """
        Load an image into a specific slot.
        
        Args:
            image_index (int): Index (0-3) of the image slot
            image_path (str): Path to the image file
            
        Returns:
            dict: Status and image info
        """
        if not 0 <= image_index <= 3:
            return {'success': False, 'error': 'Invalid image index. Must be 0-3.'}
        
        try:
            processor = self.image_processors[image_index]
            processor.load_image(image_path)
            processor.convert_to_grayscale()
            
            return {
                'success': True,
                'message': f'Image {image_index + 1} loaded successfully',
                'shape': processor.get_image_shape()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    
    def load_image_from_array(self, image_index, image_array):
        """
        Load an image from a numpy array (useful for frontend file uploads).
        
        Args:
            image_index (int): Index (0-3) of the image slot
            image_array (np.ndarray): Image data as numpy array
            
        Returns:
            dict: Status and image info
        """
        if not 0 <= image_index <= 3:
            return {'success': False, 'error': 'Invalid image index. Must be 0-3.'}
        
        try:
            processor = self.image_processors[image_index]
            processor.image = image_array.astype(np.float64)
            processor.original_image = processor.image.copy()
            processor.convert_to_grayscale()
            
            return {
                'success': True,
                'message': f'Image {image_index + 1} loaded from array',
                'shape': processor.get_image_shape()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    
    def resize_all_images(self):
        """
        Resize all loaded images to the smallest common size.
        
        Returns:
            dict: Status and target size
        """
        try:
            # Find smallest dimensions among loaded images
            loaded_processors = [p for p in self.image_processors if p.image is not None]
            
            if len(loaded_processors) == 0:
                return {'success': False, 'error': 'No images loaded'}
            
            # Find minimum dimensions
            min_height = min(p.image.shape[0] for p in loaded_processors)
            min_width = min(p.image.shape[1] for p in loaded_processors)
            target_size = (min_width, min_height)
            
            # Resize all
            for processor in loaded_processors:
                processor.resize_image(target_size)
                processor.compute_fft()
            
            return {
                'success': True,
                'message': 'All images resized and FFT computed',
                'target_size': target_size
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    
    def get_image_data(self, image_index):
        """
        Get original image data for display.
        
        Args:
            image_index (int): Index (0-3) of the image
            
        Returns:
            dict: Image data as base64 or numpy array
        """
        if not 0 <= image_index <= 3:
            return {'success': False, 'error': 'Invalid image index'}
        
        processor = self.image_processors[image_index]
        if processor.image is None:
            return {'success': False, 'error': 'No image loaded in this slot'}
        
        try:
            # Normalize image to 0-255 range
            img_normalized = ComponentVisualizer.normalize_for_display(
                processor.image, 0, 255
            ).astype(np.uint8)
            
            return {
                'success': True,
                'image_array': img_normalized,
                'shape': processor.image.shape
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    
    def get_component_data(self, image_index, component_type):
        """
        Get FFT component data for display.
        
        Args:
            image_index (int): Index (0-3) of the image
            component_type (str): 'magnitude', 'phase', 'real', or 'imaginary'
            
        Returns:
            dict: Component data as displayable array
        """
        if not 0 <= image_index <= 3:
            return {'success': False, 'error': 'Invalid image index'}
        
        processor = self.image_processors[image_index]
        if processor.fft_result is None:
            return {'success': False, 'error': 'FFT not computed for this image'}
        
        try:
            # Get raw component
            if component_type == 'magnitude':
                component = processor.get_magnitude()
            elif component_type == 'phase':
                component = processor.get_phase()
            elif component_type == 'real':
                component = processor.get_real()
            elif component_type == 'imaginary':
                component = processor.get_imaginary()
            else:
                return {'success': False, 'error': 'Invalid component type'}
            
            # Get brightness/contrast settings for this component
            settings = self.component_display_settings[image_index][component_type]
            brightness = settings['brightness']
            contrast = settings['contrast']
            
            # Prepare for display with brightness/contrast
            display_array = ComponentVisualizer.prepare_component_image(
                component, component_type, brightness=brightness, contrast=contrast
            )
            
            return {
                'success': True,
                'component_array': display_array,
                'component_type': component_type,
                'shape': display_array.shape
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    
    def get_all_components(self, image_index):
        """
        Get all four FFT components for an image.
        
        Args:
            image_index (int): Index (0-3) of the image
            
        Returns:
            dict: All components as displayable arrays
        """
        if not 0 <= image_index <= 3:
            return {'success': False, 'error': 'Invalid image index'}
        
        processor = self.image_processors[image_index]
        if processor.fft_result is None:
            return {'success': False, 'error': 'FFT not computed for this image'}
        
        try:
            components = ComponentVisualizer.prepare_all_components(processor)
            
            return {
                'success': True,
                'components': components,
                'shape': components['magnitude'].shape
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    
    def mix_images(self, settings):
        """
        Mix images based on settings and return output.
        
        Args:
            settings (dict): Mixing configuration
                {
                    'mode': 'magnitude_phase' or 'real_imaginary',
                    'weights': {
                        'magnitude': [w1, w2, w3, w4],
                        'phase': [w1, w2, w3, w4]
                    },
                    'region': {
                        'enabled': bool,
                        'size': float (0-1),
                        'type': 'inner' or 'outer'
                    },
                    'output_port': 0 or 1
                }
                
        Returns:
            dict: Mixed output image
        """
        try:
            # Validate that all images have FFT computed
            if any(p.fft_result is None for p in self.image_processors):
                return {
                    'success': False,
                    'error': 'Not all images have FFT computed. Call resize_all_images() first.'
                }
            
            # Create or reuse mixer
            if self.mixer is None:
                self.mixer = FourierMixer(self.image_processors)
            
            # Set mode
            mode = settings.get('mode', 'magnitude_phase')
            self.mixer.set_mode(mode)
            
            # Set weights
            weights = settings.get('weights', {})
            if mode == 'magnitude_phase':
                mag_weights = weights.get('magnitude', [0.25, 0.25, 0.25, 0.25])
                phase_weights = weights.get('phase', [0.25, 0.25, 0.25, 0.25])
                self.mixer.set_weights('magnitude', mag_weights)
                self.mixer.set_weights('phase', phase_weights)
            else:  # real_imaginary
                real_weights = weights.get('real', [0.25, 0.25, 0.25, 0.25])
                imag_weights = weights.get('imaginary', [0.25, 0.25, 0.25, 0.25])
                self.mixer.set_weights('real', real_weights)
                self.mixer.set_weights('imaginary', imag_weights)
            
            # Set region
            region = settings.get('region', {})
            if region.get('enabled', False):
                self.mixer.set_region(
                    size=region.get('size', 0.3),
                    region_type=region.get('type', 'inner'),
                    enabled=True
                )
            else:
                self.mixer.set_region(size=0.3, region_type='inner', enabled=False)
            
            # Compute output
            output_image = self.mixer.compute_ifft()
            
            if output_image is None:
                return {'success': False, 'error': 'Mixing was cancelled'}
            
            # Store in output port
            output_port = settings.get('output_port', 0)
            if 0 <= output_port <= 1:
                self.output_images[output_port] = output_image
            
            # Normalize for display
            output_display = ComponentVisualizer.normalize_for_display(
                output_image, 0, 255
            ).astype(np.uint8)
            
            return {
                'success': True,
                'output_array': output_display,
                'output_port': output_port,
                'shape': output_display.shape,
                'progress': 100
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    
    def mix_images_async(self, settings, callback):
            """
            Mix images asynchronously with progress updates.
            
            Args:
                settings (dict): Same as mix_images()
                callback (function): Function to call with result
            """
            if self.mixer is None:
                self.mixer = FourierMixer(self.image_processors)
            
            # Set all parameters (same as mix_images)
            mode = settings.get('mode', 'magnitude_phase')
            self.mixer.set_mode(mode)
            
            weights = settings.get('weights', {})
            if mode == 'magnitude_phase':
                self.mixer.set_weights('magnitude', weights.get('magnitude', [0.25]*4))
                self.mixer.set_weights('phase', weights.get('phase', [0.25]*4))
            else:
                self.mixer.set_weights('real', weights.get('real', [0.25]*4))
                self.mixer.set_weights('imaginary', weights.get('imaginary', [0.25]*4))
            
            region = settings.get('region', {})
            self.mixer.set_region(
                size=region.get('size', 0.3),
                region_type=region.get('type', 'inner'),
                enabled=region.get('enabled', False)
            )
            
            # Set the target output port in the mixer
            output_port = settings.get('output_port', 0)
            self.mixer.set_output_port(output_port + 1) # Mixer uses 1-based indexing internally? 
            # Actually mixer just stores it. Let's keep it consistent.
            # Ideally, we update mixer to use 0-based to match API, but let's just accept the arg.

            # --- FIX IS HERE: Added 'port_idx' argument ---
            def async_callback(output_image, port_idx):
                if output_image is not None:
                    # Use the port_idx passed back from mixer, or default to settings
                    # Note: mixer might return 1 or 2, we need 0 or 1 for array index
                    # But typically we rely on the settings passed initially.
                    
                    target_port = settings.get('output_port', 0)
                    self.output_images[target_port] = output_image
                    
                    output_display = ComponentVisualizer.normalize_for_display(
                        output_image, 0, 255
                    ).astype(np.uint8)
                    
                    result = {
                        'success': True,
                        'output_array': output_display,
                        'output_port': target_port,
                        'shape': output_display.shape
                    }
                else:
                    result = {'success': False, 'error': 'Operation was cancelled'}
                
                callback(result)
            
            # Start async operation
            self.mixer.mix_and_compute_async(async_callback)
    
    
    def get_mixing_progress(self):
        """
        Get current progress of mixing operation.
        
        Returns:
            dict: Progress information
        """
        if self.mixer is None:
            return {'progress': 0, 'is_processing': False}
        
        return {
            'progress': self.mixer.get_progress(),
            'is_processing': self.mixer.is_processing
        }
    
    
    def cancel_mixing(self):
        """
        Cancel the current mixing operation.
        
        Returns:
            dict: Cancellation status
        """
        if self.mixer and self.mixer.is_processing:
            self.mixer.cancel_operation()
            return {'success': True, 'message': 'Mixing cancelled'}
        
        return {'success': False, 'message': 'No operation in progress'}
    
    
    def get_output_image(self, output_port):
        """
        Get the mixed output image from a specific port.
        
        Args:
            output_port (int): 0 or 1
            
        Returns:
            dict: Output image data
        """
        if not 0 <= output_port <= 1:
            return {'success': False, 'error': 'Invalid output port. Must be 0 or 1.'}
        
        output = self.output_images[output_port]
        if output is None:
            return {'success': False, 'error': 'No output in this port yet'}
        
        try:
            output_display = ComponentVisualizer.normalize_for_display(
                output, 0, 255
            ).astype(np.uint8)
            
            return {
                'success': True,
                'output_array': output_display,
                'shape': output_display.shape
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    
    def apply_brightness_contrast(self, image_index, brightness, contrast):
        """
        Apply brightness/contrast adjustment to an image.
        
        Args:
            image_index (int): Index (0-3) of the image, or 4-5 for output ports
            brightness (float): Brightness adjustment (-255 to 255)
            contrast (float): Contrast multiplier (0.5 to 3.0)
            
        Returns:
            dict: Adjusted image data
        """
        try:
            if 0 <= image_index <= 3:
                # Apply to input image
                processor = self.image_processors[image_index]
                if processor.image is None:
                    return {'success': False, 'error': 'No image in this slot'}
                
                processor.apply_brightness_contrast(brightness, contrast)
                img_data = self.get_image_data(image_index)
                return img_data
                
            elif 4 <= image_index <= 5:
                # Apply to output image
                output_port = image_index - 4
                output = self.output_images[output_port]
                
                if output is None:
                    return {'success': False, 'error': 'No output in this port'}
                
                # Apply adjustment
                adjusted = output * contrast + brightness
                adjusted = np.clip(adjusted, 0, 255)
                self.output_images[output_port] = adjusted
                
                return self.get_output_image(output_port)
            else:
                return {'success': False, 'error': 'Invalid image index'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    
    def apply_component_brightness_contrast(self, image_index, component_type, brightness, contrast):
        """
        Apply brightness/contrast adjustment to an FFT component display.
        This affects only the visualization, not the actual FFT data.
        
        Args:
            image_index (int): Index (0-3) of the image
            component_type (str): 'magnitude', 'phase', 'real', or 'imaginary'
            brightness (float): Brightness adjustment (-255 to 255)
            contrast (float): Contrast multiplier (0.5 to 3.0)
            
        Returns:
            dict: Status and updated component data
        """
        if not 0 <= image_index <= 3:
            return {'success': False, 'error': 'Invalid image index. Must be 0-3.'}
        
        if component_type not in ['magnitude', 'phase', 'real', 'imaginary']:
            return {'success': False, 'error': 'Invalid component type'}
        
        processor = self.image_processors[image_index]
        if processor.fft_result is None:
            return {'success': False, 'error': 'FFT not computed for this image'}
        
        try:
            # Store the settings
            self.component_display_settings[image_index][component_type] = {
                'brightness': brightness,
                'contrast': contrast
            }
            
            # Return updated component data
            return self.get_component_data(image_index, component_type)
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    
    def get_status(self):
        """
        Get current status of all images and mixer.
        
        Returns:
            dict: Complete status information
        """
        loaded_images = [
            i for i, p in enumerate(self.image_processors) 
            if p.image is not None
        ]
        
        fft_computed = [
            i for i, p in enumerate(self.image_processors) 
            if p.fft_result is not None
        ]
        
        return {
            'loaded_images': loaded_images,
            'fft_computed': fft_computed,
            'mixer_initialized': self.mixer is not None,
            'is_processing': self.mixer.is_processing if self.mixer else False,
            'output_ports': {
                0: self.output_images[0] is not None,
                1: self.output_images[1] is not None
            }
        }
    
    
    def reset(self):
        """
        Reset the entire backend (clear all images and mixer).
        
        Returns:
            dict: Reset status
        """
        self.image_processors = [ImageProcessor() for _ in range(4)]
        self.mixer = None
        self.output_images = [None, None]
        
        # Reset component display settings
        self.component_display_settings = {}
        for i in range(4):
            self.component_display_settings[i] = {
                'magnitude': {'brightness': 0, 'contrast': 1.0},
                'phase': {'brightness': 0, 'contrast': 1.0},
                'real': {'brightness': 0, 'contrast': 1.0},
                'imaginary': {'brightness': 0, 'contrast': 1.0}
            }
        
        return {
            'success': True,
            'message': 'Backend reset successfully'
        }
    
    
    def __repr__(self):
        """String representation of BackendAPI."""
        status = self.get_status()
        return f"BackendAPI(loaded={len(status['loaded_images'])}/4, mixer={status['mixer_initialized']})"