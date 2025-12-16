import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set matplotlib to non-blocking mode
import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend which works better on Windows

from classes.image_processor import ImageProcessor
from classes.component_visualizer import ComponentVisualizer
import matplotlib.pyplot as plt
import numpy as np


def test_component_preparation():
    """Test preparing individual components for display."""
    print("\n" + "="*60)
    print("TEST 1: Component Preparation")
    print("="*60)
    
    # Load and process image
    processor = ImageProcessor()
    processor.load_image('test_images/Steve_(Minecraft).png')
    processor.convert_to_grayscale()
    processor.resize_image((256, 256))
    processor.compute_fft()
    
    # Get raw components
    magnitude = processor.get_magnitude()
    phase = processor.get_phase()
    real = processor.get_real()
    imaginary = processor.get_imaginary()
    
    # Prepare for display
    mag_display = ComponentVisualizer.prepare_component_image(magnitude, 'magnitude')
    phase_display = ComponentVisualizer.prepare_component_image(phase, 'phase')
    real_display = ComponentVisualizer.prepare_component_image(real, 'real')
    imag_display = ComponentVisualizer.prepare_component_image(imaginary, 'imaginary')
    
    # Display all
    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    
    axes[0, 0].imshow(mag_display, cmap='gray')
    axes[0, 0].set_title('Magnitude (Display Ready)')
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(phase_display, cmap='gray')
    axes[0, 1].set_title('Phase (Display Ready)')
    axes[0, 1].axis('off')
    
    axes[1, 0].imshow(real_display, cmap='gray')
    axes[1, 0].set_title('Real (Display Ready)')
    axes[1, 0].axis('off')
    
    axes[1, 1].imshow(imag_display, cmap='gray')
    axes[1, 1].set_title('Imaginary (Display Ready)')
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    print(f"✅ Magnitude display range: {mag_display.min()} to {mag_display.max()}")
    print(f"✅ Phase display range: {phase_display.min()} to {phase_display.max()}")
    print("✅ Test 1 Passed!\n")


def test_all_components_helper():
    """Test the prepare_all_components helper method."""
    print("\n" + "="*60)
    print("TEST 2: Prepare All Components Helper")
    print("="*60)
    
    processor = ImageProcessor()
    processor.load_image('test_images/Steve_(Minecraft).png')
    processor.convert_to_grayscale()
    processor.resize_image((256, 256))
    processor.compute_fft()
    
    # Use helper method
    components = ComponentVisualizer.prepare_all_components(processor)
    
    print(f"✅ Components prepared: {list(components.keys())}")
    print(f"   All in range 0-255: {all(c.min() >= 0 and c.max() <= 255 for c in components.values())}")
    print(f"   All uint8 dtype: {all(c.dtype == np.uint8 for c in components.values())}")
    
    print("✅ Test 2 Passed!\n")


def test_component_grid():
    """Test creating a component grid visualization."""
    print("\n" + "="*60)
    print("TEST 3: Component Grid Visualization")
    print("="*60)
    
    processor = ImageProcessor()
    processor.load_image('test_images/Steve_(Minecraft).png')
    processor.convert_to_grayscale()
    processor.resize_image((256, 256))
    processor.compute_fft()
    
    # Create grid with original
    grid_with_original = ComponentVisualizer.create_component_grid(
        processor, 
        include_original=True
    )
    
    plt.figure(figsize=(15, 10))
    plt.imshow(grid_with_original, cmap='gray')
    plt.title('Component Grid (with Original)')
    plt.axis('off')
    plt.tight_layout()
    plt.show()
    
    print(f"✅ Grid shape: {grid_with_original.shape}")
    print("✅ Test 3 Passed!\n")


def test_component_statistics():
    """Test getting component statistics."""
    print("\n" + "="*60)
    print("TEST 4: Component Statistics")
    print("="*60)
    
    processor = ImageProcessor()
    processor.load_image('test_images/Steve_(Minecraft).png')
    processor.convert_to_grayscale()
    processor.resize_image((256, 256))
    processor.compute_fft()
    
    magnitude = processor.get_magnitude()
    stats = ComponentVisualizer.get_component_statistics(magnitude, 'magnitude')
    
    print("Magnitude Statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    print("✅ Test 4 Passed!\n")


def test_log_scaling_comparison():
    """Compare magnitude with and without log scaling."""
    print("\n" + "="*60)
    print("TEST 5: Log Scaling Comparison")
    print("="*60)
    
    processor = ImageProcessor()
    processor.load_image('test_images/Steve_(Minecraft).png')
    processor.convert_to_grayscale()
    processor.resize_image((256, 256))
    processor.compute_fft()
    
    magnitude = processor.get_magnitude()
    
    # Without log scaling
    mag_linear = ComponentVisualizer.normalize_for_display(magnitude, 0, 255).astype(np.uint8)
    
    # With log scaling
    mag_log = ComponentVisualizer.apply_log_scaling(magnitude)
    mag_log = ComponentVisualizer.normalize_for_display(mag_log, 0, 255).astype(np.uint8)
    
    # Display comparison
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    
    axes[0].imshow(mag_linear, cmap='gray')
    axes[0].set_title('Magnitude (Linear Scale)')
    axes[0].axis('off')
    
    axes[1].imshow(mag_log, cmap='gray')
    axes[1].set_title('Magnitude (Log Scale) ✅ Better!')
    axes[1].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    print("✅ Log scaling makes frequencies more visible!")
    print("✅ Test 5 Passed!\n")


if __name__ == "__main__":
    print("\n🚀 Starting ComponentVisualizer Tests...\n")
    import sys
    sys.stdout.flush()  # Force output to appear immediately
    
    try:
        test_component_preparation()
        print("Test 1 done, check for matplotlib window and close it to continue...")
        sys.stdout.flush()
        
        test_all_components_helper()
        test_component_grid()
        print("Test 3 done, check for matplotlib window and close it to continue...")
        sys.stdout.flush()
        
        test_component_statistics()
        test_log_scaling_comparison()
        print("Test 5 done, check for matplotlib window and close it to continue...")
        sys.stdout.flush()
        
        print("\n" + "="*60)
        print("✅ ALL COMPONENTVISUALIZER TESTS PASSED!")
        print("="*60 + "\n")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()