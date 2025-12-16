import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

# Explicitly export the class to avoid any import confusion
__all__ = ["ImageProcessor"]


class ImageProcessor:
    """
    Handles loading, processing, and Fourier Transform operations on images.
    
    Attributes:
        image (np.ndarray): The current grayscale image
        fft_result (np.ndarray): Complex FFT result of the image
        original_image (np.ndarray): Backup of original image
    """
    
    def __init__(self):
        self.image = None  # Grayscale image for processing
        self.color_image = None  # Original colored image
        self.fft_result = None
        self.original_image = None
        self.image_path = None
        self.fft_cached = False  # Track if FFT is up to date
    
    
    def load_image(self, path):
        """
        Load an image from file path.
        
        Args:
            path (str): Path to the image file
            
        Returns:
            np.ndarray: Loaded image array
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            Exception: If image cannot be loaded
        """
        try:
            img = Image.open(path)
            self.image = np.array(img, dtype=np.float64)
            self.color_image = self.image.copy()  # Keep colored version
            self.original_image = self.image.copy()
            self.image_path = path
            self.fft_cached = False  # Invalidate FFT cache
            print(f"✅ Image loaded: {path}")
            print(f"   Shape: {self.image.shape}, Dtype: {self.image.dtype}")
            return self.image
        except FileNotFoundError:
            raise FileNotFoundError(f"❌ Image not found: {path}")
        except Exception as e:
            raise Exception(f"❌ Error loading image: {str(e)}")
    
    
    def convert_to_grayscale(self):
        """
        Convert the image to grayscale if it's colored.
        Uses the luminosity method: 0.299*R + 0.587*G + 0.114*B
        
        Returns:
            np.ndarray: Grayscale image
        """
        if self.image is None:
            raise ValueError("❌ No image loaded. Call load_image() first.")
        
        # Check if image is colored (has 3 channels)
        if len(self.image.shape) == 3 and self.image.shape[2] >= 3:
            # Convert to grayscale using luminosity method
            self.image = np.dot(self.image[..., :3], [0.299, 0.587, 0.114])
            # Invalidate FFT cache since image changed
            self.fft_cached = False
            self.fft_result = None
            print(f"✅ Converted to grayscale. New shape: {self.image.shape}")
        else:
            print(f"ℹ️  Image is already grayscale.")
        
        return self.image
    
    
    def resize_image(self, target_size):
        """
        Resize the image to target dimensions.
        
        Args:
            target_size (tuple): (width, height) for the new size
            
        Returns:
            np.ndarray: Resized image
        """
        if self.image is None:
            raise ValueError("❌ No image loaded. Call load_image() first.")
        
        # Convert numpy array to PIL Image for resizing
        if self.image.dtype != np.uint8:
            # Normalize to 0-255 range if needed
            img_normalized = ((self.image - self.image.min()) / 
                            (self.image.max() - self.image.min()) * 255).astype(np.uint8)
        else:
            img_normalized = self.image
        
        pil_image = Image.fromarray(img_normalized)
        
        # Resize using high-quality Lanczos resampling
        resized_pil = pil_image.resize(target_size, Image.LANCZOS)
        
        # Convert back to numpy array
        self.image = np.array(resized_pil, dtype=np.float64)
        
        # Invalidate FFT cache since image dimensions changed
        self.fft_cached = False
        self.fft_result = None
        
        print(f"✅ Image resized to: {target_size}")
        return self.image
    
    
    def compute_fft(self, force=False):
        """
        Compute the 2D Fast Fourier Transform of the image.
        Uses fftshift to center the DC component (zero frequency).
        Caches result to avoid recomputation.
        
        Args:
            force (bool): Force recomputation even if cached
        
        Returns:
            np.ndarray: Complex FFT result (centered)
        """
        if self.image is None:
            raise ValueError("❌ No image loaded. Call load_image() first.")
        
        # Return cached FFT if available and not forcing
        if self.fft_cached and not force and self.fft_result is not None:
            print(f"⚡ Using cached FFT. Shape: {self.fft_result.shape}")
            return self.fft_result
        
        # Compute 2D FFT and shift zero frequency to center
        self.fft_result = np.fft.fftshift(np.fft.fft2(self.image))
        self.fft_cached = True
        
        print(f"✅ FFT computed. Shape: {self.fft_result.shape}")
        print(f"   FFT dtype: {self.fft_result.dtype}")
        
        return self.fft_result
    
    
    def get_magnitude(self):
        """
        Get the magnitude (absolute value) of the FFT.
        
        Returns:
            np.ndarray: Magnitude spectrum
        """
        if self.fft_result is None:
            raise ValueError("❌ FFT not computed. Call compute_fft() first.")
        
        magnitude = np.abs(self.fft_result)
        return magnitude
    
    
    def get_phase(self):
        """
        Get the phase (angle) of the FFT.
        
        Returns:
            np.ndarray: Phase spectrum (in radians, range: -π to π)
        """
        if self.fft_result is None:
            raise ValueError("❌ FFT not computed. Call compute_fft() first.")
        
        phase = np.angle(self.fft_result)
        return phase
    
    
    def get_real(self):
        """
        Get the real component of the FFT.
        
        Returns:
            np.ndarray: Real part of FFT
        """
        if self.fft_result is None:
            raise ValueError("❌ FFT not computed. Call compute_fft() first.")
        
        real = np.real(self.fft_result)
        return real
    
    
    def get_imaginary(self):
        """
        Get the imaginary component of the FFT.
        
        Returns:
            np.ndarray: Imaginary part of FFT
        """
        if self.fft_result is None:
            raise ValueError("❌ FFT not computed. Call compute_fft() first.")
        
        imaginary = np.imag(self.fft_result)
        return imaginary
    
    
    def apply_brightness_contrast(self, brightness=0, contrast=1.0):
        """
        Apply brightness and contrast adjustments to the image.
        
        Args:
            brightness (float): Brightness adjustment (-255 to 255)
            contrast (float): Contrast multiplier (0.5 to 3.0 recommended)
            
        Returns:
            np.ndarray: Adjusted image
        """
        if self.image is None:
            raise ValueError("❌ No image loaded. Call load_image() first.")
        
        # Apply contrast and brightness
        adjusted = self.image * contrast + brightness
        
        # Clip values to valid range
        adjusted = np.clip(adjusted, 0, 255)
        
        self.image = adjusted
        
        print(f"✅ Brightness/Contrast applied: brightness={brightness}, contrast={contrast}")
        return self.image
    
    
    def get_image_shape(self):
        """Get the current image shape."""
        if self.image is None:
            return None
        return self.image.shape
    
    
    def reset_to_original(self):
        """Reset image to original loaded state."""
        if self.original_image is not None:
            self.image = self.original_image.copy()
            print("✅ Image reset to original")
        else:
            print("⚠️  No original image to reset to")
    
    
    def display_image(self, title="Image"):
        """
        Display the current image using matplotlib.
        
        Args:
            title (str): Title for the plot
        """
        if self.image is None:
            raise ValueError("❌ No image to display.")
        
        plt.figure(figsize=(6, 6))
        plt.imshow(self.image, cmap='gray')
        plt.title(title)
        plt.colorbar()
        plt.axis('off')
        plt.tight_layout()
        plt.show()
    
    
    def display_fft_components(self):
        """
        Display all four FFT components in a grid.
        """
        if self.fft_result is None:
            raise ValueError("❌ FFT not computed. Call compute_fft() first.")
        
        magnitude = self.get_magnitude()
        phase = self.get_phase()
        real = self.get_real()
        imaginary = self.get_imaginary()
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        
        # Original Image
        axes[0, 0].imshow(self.image, cmap='gray')
        axes[0, 0].set_title('Original Image')
        axes[0, 0].axis('off')
        
        # Magnitude (log scale for better visualization)
        axes[0, 1].imshow(np.log(1 + magnitude), cmap='gray')
        axes[0, 1].set_title('FFT Magnitude (log scale)')
        axes[0, 1].axis('off')
        
        # Phase
        axes[0, 2].imshow(phase, cmap='gray')
        axes[0, 2].set_title('FFT Phase')
        axes[0, 2].axis('off')
        
        # Real
        axes[1, 0].imshow(real, cmap='gray')
        axes[1, 0].set_title('FFT Real Component')
        axes[1, 0].axis('off')
        
        # Imaginary
        axes[1, 1].imshow(imaginary, cmap='gray')
        axes[1, 1].set_title('FFT Imaginary Component')
        axes[1, 1].axis('off')
        
        # Hide the last subplot
        axes[1, 2].axis('off')
        
        plt.tight_layout()
        plt.show()
    
    
    def __repr__(self):
        """String representation of the ImageProcessor."""
        if self.image is None:
            return "ImageProcessor(no image loaded)"
        return f"ImageProcessor(shape={self.image.shape}, path='{self.image_path}')"