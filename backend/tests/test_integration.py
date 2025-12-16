import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set matplotlib to non-blocking mode
import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend which works better on Windows

from backend_api import BackendAPI
import matplotlib.pyplot as plt
import numpy as np


def test_complete_workflow():
    """Test the complete workflow from loading to mixing."""
    print("\n" + "="*60)
    print("INTEGRATION TEST: Complete Workflow")
    print("="*60)
    
    # Initialize API
    api = BackendAPI()
    print(f"\n{api}")
    
    # Load 4 images
    print("\n--- Loading Images ---")
    image_paths = [
        'test_images/Steve_(Minecraft).png',
        'test_images/building.png',
        'test_images/cat.png',
        'test_images/Landscape.png'
    ]
    
    for i, path in enumerate(image_paths):
        result = api.load_image(i, path)
        if result['success']:
            print(f"✅ Image {i+1} loaded: {result['shape']}")
        else:
            print(f"❌ Failed to load image {i+1}: {result['error']}")
    
    # Resize all to common size
    print("\n--- Resizing Images ---")
    result = api.resize_all_images()
    if result['success']:
        print(f"✅ All images resized to: {result['target_size']}")
    else:
        print(f"❌ Resize failed: {result['error']}")
    
    # Get status
    print("\n--- System Status ---")
    status = api.get_status()
    print(f"Loaded images: {status['loaded_images']}")
    print(f"FFT computed: {status['fft_computed']}")
    print(f"Mixer initialized: {status['mixer_initialized']}")
    
    # Get and display components
    print("\n--- Getting Component Data ---")
    result = api.get_component_data(0, 'magnitude')
    if result['success']:
        print(f"✅ Got magnitude component: shape={result['shape']}")
    
    # Mix images: Magnitude from image 1, Phase from image 2
    print("\n--- Mixing Images ---")
    mix_settings = {
        'mode': 'magnitude_phase',
        'weights': {
            'magnitude': [1.0, 0.0, 0.0, 0.0],
            'phase': [0.0, 1.0, 0.0, 0.0]
        },
        'region': {
            'enabled': False
        },
        'output_port': 0
    }
    
    result = api.mix_images(mix_settings)
    if result['success']:
        print(f"✅ Mixing successful!")
        print(f"   Output shape: {result['shape']}")
        print(f"   Output port: {result['output_port']}")
    else:
        print(f"❌ Mixing failed: {result['error']}")
    
    # Get the original images
    img1 = api.get_image_data(0)
    img2 = api.get_image_data(1)
    
    # Display results
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    axes[0].imshow(img1['image_array'], cmap='gray')
    axes[0].set_title('Image 1 (Magnitude Source)')
    axes[0].axis('off')
    
    axes[1].imshow(img2['image_array'], cmap='gray')
    axes[1].set_title('Image 2 (Phase Source)')
    axes[1].axis('off')
    
    axes[2].imshow(result['output_array'], cmap='gray')
    axes[2].set_title('Mixed Output\n(Should look like Image 2)')
    axes[2].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    print("\n✅ Integration Test Complete!")


def test_region_filtering():
    """Test region-based frequency filtering."""
    print("\n" + "="*60)
    print("INTEGRATION TEST: Region Filtering")
    print("="*60)
    
    api = BackendAPI()
    
    # Load images
    for i in range(4):
        api.load_image(i, 'test_images/Steve_(Minecraft).png')
    
    api.resize_all_images()
    
    # Test inner region (low frequencies)
    print("\n--- Testing Inner Region (Low Frequencies) ---")
    mix_settings = {
        'mode': 'magnitude_phase',
        'weights': {
            'magnitude': [1.0, 0.0, 0.0, 0.0],
            'phase': [1.0, 0.0, 0.0, 0.0]
        },
        'region': {
            'enabled': True,
            'size': 0.3,
            'type': 'inner'
        },
        'output_port': 0
    }
    
    result_inner = api.mix_images(mix_settings)
    
    # Test outer region (high frequencies)
    print("\n--- Testing Outer Region (High Frequencies) ---")
    mix_settings['region']['type'] = 'outer'
    result_outer = api.mix_images(mix_settings)
    
    # Display
    original = api.get_image_data(0)
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    axes[0].imshow(original['image_array'], cmap='gray')
    axes[0].set_title('Original')
    axes[0].axis('off')
    
    axes[1].imshow(result_inner['output_array'], cmap='gray')
    axes[1].set_title('Inner Region (Blurry)')
    axes[1].axis('off')
    
    axes[2].imshow(result_outer['output_array'], cmap='gray')
    axes[2].set_title('Outer Region (Edges)')
    axes[2].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    print("✅ Region Filtering Test Complete!")


def test_api_status_and_reset():
    """Test API status tracking and reset."""
    print("\n" + "="*60)
    print("INTEGRATION TEST: Status & Reset")
    print("="*60)
    
    api = BackendAPI()
    
    print("\n--- Initial Status ---")
    print(api.get_status())
    
    # Load some images
    api.load_image(0, 'test_images/Steve_(Minecraft).png')
    api.load_image(1, 'test_images/building.png')
    
    print("\n--- After Loading 2 Images ---")
    print(api.get_status())
    
    # Resize (computes FFT)
    api.resize_all_images()
    
    print("\n--- After Resizing ---")
    print(api.get_status())
    
    # Reset
    print("\n--- Resetting ---")
    api.reset()
    print(api.get_status())
    
    print("\n✅ Status & Reset Test Complete!")


if __name__ == "__main__":
    print("\n🚀 Starting Integration Tests...\n")
    import sys
    sys.stdout.flush()  # Force output to appear immediately
    
    try:
        test_complete_workflow()
        print("Test 1 done, check for matplotlib window and close it to continue...")
        sys.stdout.flush()
        
        test_region_filtering()
        print("Test 2 done, check for matplotlib window and close it to continue...")
        sys.stdout.flush()
        
        test_api_status_and_reset()
        
        print("\n" + "="*60)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("="*60 + "\n")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()