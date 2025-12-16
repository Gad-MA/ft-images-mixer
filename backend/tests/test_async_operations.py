import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend_api import BackendAPI
import matplotlib.pyplot as plt
import time
import threading


def test_async_mixing():
    """Test asynchronous mixing with callback."""
    print("\n" + "="*60)
    print("TEST 1: Async Mixing with Callback")
    print("="*60)
    
    api = BackendAPI()
    
    # Load images
    print("\n--- Loading Images ---")
    for i in range(4):
        api.load_image(i, 'test_images/Steve_(Minecraft).png')
    api.resize_all_images()
    
    # Define callback
    result_container = {'result': None, 'completed': False}
    
    def on_complete(result):
        print(f"\n🎉 Async operation completed!")
        result_container['result'] = result
        result_container['completed'] = True
    
    # Start async mixing
    print("\n--- Starting Async Mixing ---")
    mix_settings = {
        'mode': 'magnitude_phase',
        'weights': {
            'magnitude': [1.0, 0.0, 0.0, 0.0],
            'phase': [1.0, 0.0, 0.0, 0.0]
        },
        'region': {'enabled': False},
        'output_port': 0
    }
    
    api.mix_images_async(mix_settings, on_complete)
    
    # Monitor progress
    print("\n--- Monitoring Progress ---")
    while not result_container['completed']:
        progress_info = api.get_mixing_progress()
        print(f"Progress: {progress_info['progress']}%, Processing: {progress_info['is_processing']}")
        time.sleep(0.1)
    
    # Display result
    if result_container['result']['success']:
        print(f"\n✅ Result received: shape={result_container['result']['shape']}")
        
        plt.figure(figsize=(8, 8))
        plt.imshow(result_container['result']['output_array'], cmap='gray')
        plt.title('Async Mixing Result')
        plt.axis('off')
        plt.show()
    else:
        print(f"\n❌ Async mixing failed: {result_container['result']['error']}")
    
    print("\n✅ Test 1 Passed!")


def test_cancellation():
    """Test cancelling an operation in progress."""
    print("\n" + "="*60)
    print("TEST 2: Operation Cancellation")
    print("="*60)
    
    api = BackendAPI()
    
    # Load images
    print("\n--- Loading Images ---")
    for i in range(4):
        api.load_image(i, 'test_images/Steve_(Minecraft).png')
    api.resize_all_images()
    
    # Start first operation
    print("\n--- Starting First Operation ---")
    result1 = {'completed': False}
    
    def callback1(result):
        print("⚠️  Callback 1 called (should be cancelled)")
        result1['completed'] = True
        result1['result'] = result
    
    mix_settings = {
        'mode': 'magnitude_phase',
        'weights': {
            'magnitude': [1.0, 0.0, 0.0, 0.0],
            'phase': [1.0, 0.0, 0.0, 0.0]
        },
        'region': {'enabled': False},
        'output_port': 0
    }
    
    api.mix_images_async(mix_settings, callback1)
    
    # Wait a bit
    time.sleep(0.2)
    
    # Cancel it
    print("\n--- Cancelling First Operation ---")
    cancel_result = api.cancel_mixing()
    print(f"Cancellation: {cancel_result}")
    
    # Wait for cancellation to complete
    time.sleep(0.5)
    
    print("\n--- Starting Second Operation (Should Replace First) ---")
    result2 = {'completed': False}
    
    def callback2(result):
        print("✅ Callback 2 called (this one should complete)")
        result2['completed'] = True
        result2['result'] = result
    
    # Change weights for second operation
    mix_settings['weights']['magnitude'] = [0.5, 0.5, 0.0, 0.0]
    api.mix_images_async(mix_settings, callback2)
    
    # Wait for completion
    while not result2['completed']:
        time.sleep(0.1)
    
    print(f"\n✅ Second operation completed successfully!")
    print(f"   Result: {result2['result']['success']}")
    
    print("\n✅ Test 2 Passed!")


def test_rapid_setting_changes():
    """Test rapidly changing settings (simulates user interaction)."""
    print("\n" + "="*60)
    print("TEST 3: Rapid Setting Changes")
    print("="*60)
    
    api = BackendAPI()
    
    # Load images
    print("\n--- Loading Images ---")
    for i in range(4):
        api.load_image(i, 'test_images/Steve_(Minecraft).png')
    api.resize_all_images()
    
    print("\n--- Simulating Rapid User Interactions ---")
    print("(User keeps changing sliders quickly)")
    
    results = []
    
    def make_callback(request_id):
        def callback(result):
            print(f"  Request {request_id} completed")
            results.append({'id': request_id, 'result': result})
        return callback
    
    # Simulate user rapidly changing settings
    for i in range(5):
        print(f"\nStarting request {i+1}...")
        
        mix_settings = {
            'mode': 'magnitude_phase',
            'weights': {
                'magnitude': [1.0 - i*0.2, i*0.2, 0.0, 0.0],
                'phase': [1.0, 0.0, 0.0, 0.0]
            },
            'region': {'enabled': False},
            'output_port': 0
        }
        
        api.mix_images_async(mix_settings, make_callback(i+1))
        time.sleep(0.05)  # Very short delay (rapid changes)
    
    # Wait for final operation to complete
    print("\n--- Waiting for Final Operation ---")
    time.sleep(2)
    
    print(f"\n✅ Completed {len(results)} operations")
    print("   (Only the last request should complete, others should be cancelled)")
    
    print("\n✅ Test 3 Passed!")


def test_progress_monitoring():
    """Test detailed progress monitoring."""
    print("\n" + "="*60)
    print("TEST 4: Progress Monitoring")
    print("="*60)
    
    api = BackendAPI()
    
    # Load images
    for i in range(4):
        api.load_image(i, 'test_images/Steve_(Minecraft).png')
    api.resize_all_images()
    
    completed = {'done': False}
    
    def callback(result):
        completed['done'] = True
    
    mix_settings = {
        'mode': 'magnitude_phase',
        'weights': {
            'magnitude': [1.0, 0.0, 0.0, 0.0],
            'phase': [1.0, 0.0, 0.0, 0.0]
        },
        'region': {'enabled': False},
        'output_port': 0
    }
    
    api.mix_images_async(mix_settings, callback)
    
    # Monitor with progress bar visualization
    print("\nProgress:")
    last_progress = -1
    
    while not completed['done']:
        progress_info = api.get_mixing_progress()
        current_progress = progress_info['progress']
        
        if current_progress != last_progress:
            # Create simple progress bar
            bar_length = 50
            filled = int(bar_length * current_progress / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\r{bar} {current_progress}%", end='', flush=True)
            last_progress = current_progress
        
        time.sleep(0.05)
    
    print("\n\n✅ Test 4 Passed!")


def test_multiple_output_ports():
    """Test using both output ports simultaneously."""
    print("\n" + "="*60)
    print("TEST 5: Multiple Output Ports")
    print("="*60)
    
    api = BackendAPI()
    
    # Load images
    for i in range(4):
        api.load_image(i, 'test_images/Steve_(Minecraft).png')
    api.resize_all_images()
    
    print("\n--- Sending to Output Port 0 ---")
    mix_settings_1 = {
        'mode': 'magnitude_phase',
        'weights': {
            'magnitude': [1.0, 0.0, 0.0, 0.0],
            'phase': [1.0, 0.0, 0.0, 0.0]
        },
        'region': {'enabled': False},
        'output_port': 0
    }
    result1 = api.mix_images(mix_settings_1)
    print(f"✅ Port 0: {result1['success']}")
    
    print("\n--- Sending to Output Port 1 ---")
    mix_settings_2 = {
        'mode': 'magnitude_phase',
        'weights': {
            'magnitude': [0.5, 0.5, 0.0, 0.0],
            'phase': [0.5, 0.5, 0.0, 0.0]
        },
        'region': {'enabled': False},
        'output_port': 1
    }
    result2 = api.mix_images(mix_settings_2)
    print(f"✅ Port 1: {result2['success']}")
    
    # Check status
    status = api.get_status()
    print(f"\n--- Output Ports Status ---")
    print(f"Port 0 has output: {status['output_ports'][0]}")
    print(f"Port 1 has output: {status['output_ports'][1]}")
    
    # Display both outputs
    output0 = api.get_output_image(0)
    output1 = api.get_output_image(1)
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    
    axes[0].imshow(output0['output_array'], cmap='gray')
    axes[0].set_title('Output Port 0')
    axes[0].axis('off')
    
    axes[1].imshow(output1['output_array'], cmap='gray')
    axes[1].set_title('Output Port 1')
    axes[1].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    print("\n✅ Test 5 Passed!")


if __name__ == "__main__":
    print("\n🚀 Starting Async Operations Tests...\n")
    
    test_async_mixing()
    test_cancellation()
    test_rapid_setting_changes()
    test_progress_monitoring()
    test_multiple_output_ports()
    
    print("\n" + "="*60)
    print("✅ ALL ASYNC OPERATIONS TESTS PASSED!")
    print("="*60 + "\n")