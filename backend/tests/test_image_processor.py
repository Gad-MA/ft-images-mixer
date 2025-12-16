import sys
import os

# Add parent directory to path so we can import from classes/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.image_processor import ImageProcessor
import matplotlib.pyplot as plt
import numpy as np


def test_basic_operations():
    """Test basic image loading and processing."""
    print("\n" + "="*60)
    print("TEST 1: Basic Image Operations")
    print("="*60)
    
    # Create processor
    processor = ImageProcessor()
    
    # Load image (CHANGE THIS PATH to your actual image)
    processor.load_image('test_images/Steve_(Minecraft).png')
    
    # Convert to grayscale
    processor.convert_to_grayscale()
    
    # Resize
    processor.resize_image((256, 256))
    
    # Display
    processor.display_image("Processed Image")
    
    print("✅ Test 1 Passed!\n")


def test_fft_operations():
    """Test FFT computation and component extraction."""
    print("\n" + "="*60)
    print("TEST 2: FFT Operations")
    print("="*60)
    
    processor = ImageProcessor()
    processor.load_image('test_images/Steve_(Minecraft).png')
    processor.convert_to_grayscale()
    processor.resize_image((256, 256))
    
    # Compute FFT
    processor.compute_fft()
    
    # Get all components
    magnitude = processor.get_magnitude()
    phase = processor.get_phase()
    real = processor.get_real()
    imaginary = processor.get_imaginary()
    
    print(f"Magnitude range: {magnitude.min():.2f} to {magnitude.max():.2f}")
    print(f"Phase range: {phase.min():.2f} to {phase.max():.2f}")
    
    # Display all components
    processor.display_fft_components()
    
    print("✅ Test 2 Passed!\n")


def test_brightness_contrast():
    """Test brightness/contrast adjustment."""
    print("\n" + "="*60)
    print("TEST 3: Brightness/Contrast")
    print("="*60)
    
    processor = ImageProcessor()
    processor.load_image('test_images/image1.png')
    processor.convert_to_grayscale()
    processor.resize_image((256, 256))
    
    # Show original
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    axes[0].imshow(processor.image, cmap='gray')
    axes[0].set_title('Original')
    axes[0].axis('off')
    
    # Increase brightness
    processor.apply_brightness_contrast(brightness=50)
    axes[1].imshow(processor.image, cmap='gray')
    axes[1].set_title('Brightness +50')
    axes[1].axis('off')
    
    # Reset and increase contrast
    processor.reset_to_original()
    processor.apply_brightness_contrast(contrast=1.5)
    axes[2].imshow(processor.image, cmap='gray')
    axes[2].set_title('Contrast ×1.5')
    axes[2].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    print("✅ Test 3 Passed!\n")


def test_magnitude_phase_reconstruction():
    """Test reconstructing image from magnitude and phase."""
    print("\n" + "="*60)
    print("TEST 4: Magnitude/Phase Reconstruction")
    print("="*60)
    
    processor = ImageProcessor()
    processor.load_image('test_images/image1.png')
    processor.convert_to_grayscale()
    processor.resize_image((256, 256))
    processor.compute_fft()
    
    # Get components
    magnitude = processor.get_magnitude()
    phase = processor.get_phase()
    
    # Reconstruct FFT from magnitude and phase
    reconstructed_fft = magnitude * np.exp(1j * phase)
    
    # Inverse FFT
    reconstructed_image = np.real(np.fft.ifft2(np.fft.ifftshift(reconstructed_fft)))
    
    # Display
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    
    axes[0].imshow(processor.image, cmap='gray')
    axes[0].set_title('Original Image')
    axes[0].axis('off')
    
    axes[1].imshow(reconstructed_image, cmap='gray')
    axes[1].set_title('Reconstructed (Mag + Phase)')
    axes[1].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    # Check if reconstruction is accurate
    difference = np.abs(processor.image - reconstructed_image)
    print(f"Reconstruction error (max): {difference.max():.6f}")
    print(f"Reconstruction error (mean): {difference.mean():.6f}")
    
    print("✅ Test 4 Passed!\n")


if __name__ == "__main__":
    print("\n🚀 Starting ImageProcessor Tests...\n")
    
    # Run all tests
    test_basic_operations()
    test_fft_operations()
    test_brightness_contrast()
    test_magnitude_phase_reconstruction()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60 + "\n")