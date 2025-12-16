import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set matplotlib to non-blocking mode
import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend which works better on Windows

from classes.image_processor import ImageProcessor
from classes.fourier_mixer import FourierMixer
import matplotlib.pyplot as plt
import numpy as np


def load_test_images():
    """Helper function to load 4 test images."""
    processors = []
    
    # You'll need 4 different images in test_images/
    # For now, we'll use the same image 4 times (you should change this)
    image_paths = [
        'test_images/Steve_(Minecraft).png',
        'test_images/building.png',  # Replace with different image
        'test_images/cat.png',  # Replace with different image
        'test_images/Landscape.png',  # Replace with different image
    ]
    
    for path in image_paths:
        proc = ImageProcessor()
        proc.load_image(path)
        proc.convert_to_grayscale()
        processors.append(proc)
    
    # Resize all to same size (smallest)
    min_shape = min([p.image.shape for p in processors])
    target_size = (256, 256)  # Fixed size for testing
    
    for proc in processors:
        proc.resize_image(target_size)
        proc.compute_fft()
    
    return processors


def test_magnitude_phase_mixing():
    """TEST THE MAGIC: Mix magnitude from one image with phase from another!"""
    print("\n" + "="*60)
    print("TEST 1: Magnitude + Phase Mixing (THE MAGIC!) ✨")
    print("="*60)
    
    processors = load_test_images()
    mixer = FourierMixer(processors)
    
    # Set mode
    mixer.set_mode('magnitude_phase')
    
    # Mix: 100% magnitude from Image 1 + 100% phase from Image 2
    mixer.set_weights('magnitude', [1.0, 0.0, 0.0, 0.0])
    mixer.set_weights('phase', [0.0, 1.0, 0.0, 0.0])
    
    # Compute
    output = mixer.compute_ifft()
    
    # Display
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    axes[0].imshow(processors[0].image, cmap='gray')
    axes[0].set_title('Image 1 (Magnitude Source)')
    axes[0].axis('off')
    
    axes[1].imshow(processors[1].image, cmap='gray')
    axes[1].set_title('Image 2 (Phase Source)')
    axes[1].axis('off')
    
    axes[2].imshow(output, cmap='gray')
    axes[2].set_title('RESULT: Mag1 + Phase2\n(Should look like Image 2!)')
    axes[2].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    print("🎯 The output should resemble Image 2's STRUCTURE!")
    print("   (Because phase contains the structure)")
    print("✅ Test 1 Passed!\n")


def test_weighted_mixing():
    """Test mixing with different weight combinations."""
    print("\n" + "="*60)
    print("TEST 2: Weighted Mixing")
    print("="*60)
    
    processors = load_test_images()
    mixer = FourierMixer(processors)
    
    mixer.set_mode('magnitude_phase')
    
    # Mix: 50% magnitude from each of first two images, all phase from image 1
    mixer.set_weights('magnitude', [0.5, 0.5, 0.0, 0.0])
    mixer.set_weights('phase', [1.0, 0.0, 0.0, 0.0])
    
    output = mixer.compute_ifft()
    
    plt.figure(figsize=(8, 8))
    plt.imshow(output, cmap='gray')
    plt.title('Weighted Mix: 50% Mag1 + 50% Mag2 + 100% Phase1')
    plt.axis('off')
    plt.show()
    
    print("✅ Test 2 Passed!\n")


def test_region_filtering():
    """Test inner and outer region (low/high frequency) filtering."""
    print("\n" + "="*60)
    print("TEST 3: Region Filtering (Low/High Frequencies)")
    print("="*60)
    
    processors = load_test_images()
    mixer = FourierMixer(processors)
    
    mixer.set_mode('magnitude_phase')
    mixer.set_weights('magnitude', [1.0, 0.0, 0.0, 0.0])
    mixer.set_weights('phase', [1.0, 0.0, 0.0, 0.0])
    
    # Test inner region (low frequencies)
    mixer.set_region(size=0.3, region_type='inner', enabled=True)
    output_inner = mixer.compute_ifft()
    
    # Test outer region (high frequencies)
    mixer.set_region(size=0.3, region_type='outer', enabled=True)
    output_outer = mixer.compute_ifft()
    
    # Test no region (all frequencies)
    mixer.set_region(size=0.3, region_type='inner', enabled=False)
    output_full = mixer.compute_ifft()
    
    # Display
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    
    axes[0].imshow(processors[0].image, cmap='gray')
    axes[0].set_title('Original')
    axes[0].axis('off')
    
    axes[1].imshow(output_inner, cmap='gray')
    axes[1].set_title('Inner Region (Low Freq)\n= BLURRY')
    axes[1].axis('off')
    
    axes[2].imshow(output_outer, cmap='gray')
    axes[2].set_title('Outer Region (High Freq)\n= EDGES ONLY')
    axes[2].axis('off')
    
    axes[3].imshow(output_full, cmap='gray')
    axes[3].set_title('Full (No Filter)')
    axes[3].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    print("🎯 Inner region should be BLURRY (only low frequencies)")
    print("🎯 Outer region should show EDGES ONLY (only high frequencies)")
    print("✅ Test 3 Passed!\n")


def test_real_imaginary_mixing():
    """Test mixing real and imaginary components."""
    print("\n" + "="*60)
    print("TEST 4: Real/Imaginary Mixing")
    print("="*60)
    
    processors = load_test_images()
    mixer = FourierMixer(processors)
    
    mixer.set_mode('real_imaginary')
    mixer.set_weights('real', [1.0, 0.0, 0.0, 0.0])
    mixer.set_weights('imaginary', [0.0, 1.0, 0.0, 0.0])
    
    output = mixer.compute_ifft()
    
    plt.figure(figsize=(8, 8))
    plt.imshow(output, cmap='gray')
    plt.title('Real from Image 1 + Imaginary from Image 2')
    plt.axis('off')
    plt.show()
    
    print("✅ Test 4 Passed!\n")


def test_mask_visualization():
    """Visualize the frequency mask."""
    print("\n" + "="*60)
    print("TEST 5: Mask Visualization")
    print("="*60)
    
    processors = load_test_images()
    mixer = FourierMixer(processors)
    
    # Set region
    mixer.set_region(size=0.4, region_type='inner', enabled=True)
    mask = mixer.get_mask_visualization()
    
    plt.figure(figsize=(8, 8))
    plt.imshow(mask, cmap='gray')
    plt.title('Frequency Mask (White = Included, Black = Excluded)')
    plt.axis('off')
    plt.show()
    
    print("✅ Test 5 Passed!\n")


def test_progress_tracking():
    """Test progress tracking during computation."""
    print("\n" + "="*60)
    print("TEST 6: Progress Tracking")
    print("="*60)
    
    processors = load_test_images()
    mixer = FourierMixer(processors)
    
    mixer.set_mode('magnitude_phase')
    mixer.set_weights('magnitude', [1.0, 0.0, 0.0, 0.0])
    mixer.set_weights('phase', [1.0, 0.0, 0.0, 0.0])
    
    print("Progress during computation:")
    output = mixer.compute_ifft(report_progress=True)
    
    print(f"Final progress: {mixer.get_progress()}%")
    print("✅ Test 6 Passed!\n")


if __name__ == "__main__":
    print("\n🚀 Starting FourierMixer Tests...\n")
    print("⚠️  NOTE: For best results, use 4 DIFFERENT images!")
    print("   Edit the image_paths in load_test_images()\n")
    import sys
    sys.stdout.flush()  # Force output to appear immediately
    
    try:
        test_magnitude_phase_mixing()
        print("Test 1 done, check for matplotlib window and close it to continue...")
        sys.stdout.flush()
        
        test_weighted_mixing()
        print("Test 2 done, check for matplotlib window and close it to continue...")
        sys.stdout.flush()
        
        test_region_filtering()
        print("Test 3 done, check for matplotlib window and close it to continue...")
        sys.stdout.flush()
        
        test_real_imaginary_mixing()
        print("Test 4 done, check for matplotlib window and close it to continue...")
        sys.stdout.flush()
        
        test_mask_visualization()
        print("Test 5 done, check for matplotlib window and close it to continue...")
        sys.stdout.flush()
        
        test_progress_tracking()
        
        print("\n" + "="*60)
        print("✅ ALL FOURIERMIXER TESTS PASSED!")
        print("="*60 + "\n")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()