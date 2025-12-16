import numpy as np

# Explicitly export the class
__all__ = ["ComponentVisualizer"]


class ComponentVisualizer:
    """
    Handles visualization preparation for FFT components.
    Normalizes and scales components for proper display.
    """
    
    @staticmethod
    def normalize_for_display(array, min_val=0, max_val=255):
        """
        Normalize array to a specific range for display.
        
        Args:
            array (np.ndarray): Input array
            min_val (float): Minimum value of output range
            max_val (float): Maximum value of output range
            
        Returns:
            np.ndarray: Normalized array
        """
        # Handle edge case: all values are the same
        if array.max() == array.min():
            return np.full_like(array, (min_val + max_val) / 2, dtype=np.float64)
        
        # Normalize to 0-1 range first
        normalized = (array - array.min()) / (array.max() - array.min())
        
        # Scale to desired range
        scaled = normalized * (max_val - min_val) + min_val
        
        return scaled
    
    
    @staticmethod
    def apply_log_scaling(magnitude):
        """
        Apply logarithmic scaling to magnitude for better visualization.
        Uses log(1 + magnitude) to handle zero values and compress dynamic range.
        
        Args:
            magnitude (np.ndarray): FFT magnitude spectrum
            
        Returns:
            np.ndarray: Log-scaled magnitude
        """
        # Apply log scaling: log(1 + x)
        # The +1 ensures we don't take log of zero
        log_magnitude = np.log(1 + magnitude)
        
        return log_magnitude
    
    
    @staticmethod
    def prepare_component_image(component, component_type, brightness=0, contrast=1.0):
        """
        Prepare FFT component for display based on its type.
        Applies appropriate scaling and normalization.
        
        Args:
            component (np.ndarray): FFT component (magnitude, phase, real, or imaginary)
            component_type (str): Type of component - 'magnitude', 'phase', 'real', 'imaginary'
            brightness (float): Brightness adjustment (-255 to 255) for display
            contrast (float): Contrast multiplier (0.5 to 3.0) for display
            
        Returns:
            np.ndarray: Display-ready image (0-255 range, uint8)
            
        Raises:
            ValueError: If component_type is not recognized
        """
        valid_types = ['magnitude', 'phase', 'real', 'imaginary']
        
        if component_type not in valid_types:
            raise ValueError(f"Invalid component_type: {component_type}. "
                           f"Must be one of {valid_types}")
        
        if component_type == 'magnitude':
            # Apply log scaling for magnitude
            processed = ComponentVisualizer.apply_log_scaling(component)
            # Normalize to 0-255
            display_image = ComponentVisualizer.normalize_for_display(processed, 0, 255)
            
        elif component_type == 'phase':
            # Phase is already in range [-π, π]
            # Normalize to 0-255 for display
            display_image = ComponentVisualizer.normalize_for_display(component, 0, 255)
            
        elif component_type == 'real':
            # Real component can have positive and negative values
            # Normalize to 0-255
            display_image = ComponentVisualizer.normalize_for_display(component, 0, 255)
            
        elif component_type == 'imaginary':
            # Imaginary component can have positive and negative values
            # Normalize to 0-255
            display_image = ComponentVisualizer.normalize_for_display(component, 0, 255)
        
        # Apply brightness and contrast (window/level adjustment)
        if brightness != 0 or contrast != 1.0:
            display_image = display_image.astype(np.float64)
            display_image = display_image * contrast + brightness
            display_image = np.clip(display_image, 0, 255)
        
        # Convert to uint8 for display
        display_image = display_image.astype(np.uint8)
        
        return display_image
    
    
    @staticmethod
    def prepare_all_components(image_processor):
        """
        Prepare all four FFT components from an ImageProcessor instance.
        
        Args:
            image_processor: ImageProcessor instance with computed FFT
            
        Returns:
            dict: Dictionary containing all prepared components
                {
                    'magnitude': np.ndarray,
                    'phase': np.ndarray,
                    'real': np.ndarray,
                    'imaginary': np.ndarray
                }
        """
        if image_processor.fft_result is None:
            raise ValueError("FFT not computed in ImageProcessor")
        
        # Get raw components
        magnitude = image_processor.get_magnitude()
        phase = image_processor.get_phase()
        real = image_processor.get_real()
        imaginary = image_processor.get_imaginary()
        
        # Prepare each for display
        prepared = {
            'magnitude': ComponentVisualizer.prepare_component_image(magnitude, 'magnitude'),
            'phase': ComponentVisualizer.prepare_component_image(phase, 'phase'),
            'real': ComponentVisualizer.prepare_component_image(real, 'real'),
            'imaginary': ComponentVisualizer.prepare_component_image(imaginary, 'imaginary')
        }
        
        return prepared
    
    
    @staticmethod
    def create_component_grid(image_processor, include_original=True):
        """
        Create a grid visualization of all components.
        
        Args:
            image_processor: ImageProcessor instance
            include_original (bool): Whether to include original image in grid
            
        Returns:
            np.ndarray: Grid image suitable for display
        """
        components = ComponentVisualizer.prepare_all_components(image_processor)
        
        if include_original:
            # Normalize original image
            original = ComponentVisualizer.normalize_for_display(
                image_processor.image, 0, 255
            ).astype(np.uint8)
            
            # Create 2x3 grid: [Original, Magnitude, Phase]
            #                   [Real, Imaginary, Empty]
            top_row = np.hstack([
                original,
                components['magnitude'],
                components['phase']
            ])
            
            bottom_row = np.hstack([
                components['real'],
                components['imaginary'],
                np.zeros_like(components['real'])  # Empty space
            ])
            
            grid = np.vstack([top_row, bottom_row])
        else:
            # Create 2x2 grid: [Magnitude, Phase]
            #                   [Real, Imaginary]
            top_row = np.hstack([
                components['magnitude'],
                components['phase']
            ])
            
            bottom_row = np.hstack([
                components['real'],
                components['imaginary']
            ])
            
            grid = np.vstack([top_row, bottom_row])
        
        return grid
    
    
    @staticmethod
    def get_component_statistics(component, component_type):
        """
        Get statistical information about a component.
        
        Args:
            component (np.ndarray): FFT component
            component_type (str): Type of component
            
        Returns:
            dict: Statistics dictionary
        """
        stats = {
            'type': component_type,
            'shape': component.shape,
            'min': float(component.min()),
            'max': float(component.max()),
            'mean': float(component.mean()),
            'std': float(component.std()),
            'median': float(np.median(component))
        }
        
        return stats