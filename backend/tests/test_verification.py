# File: tests/test_verification.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.image_processor import ImageProcessor
import numpy as np
import matplotlib.pyplot as plt


def test_perfect_reconstruction():
    """
    TEST: FFT → IFFT should give back original image
    PASS CRITERIA: Reconstruction error < 0.001
    """
    print("\n" + "="*60)
    print("TEST 1: Perfect Reconstruction (FFT → IFFT)")
    print("="*60)
    
    # Load image
    processor = ImageProcessor()
    processor.load_image('test_images/Steve_(Minecraft).png')
    processor.convert_to_grayscale()
    processor.resize_image((256, 256))
    
    original_image = processor.image.copy()
    
    # Compute FFT
    processor.compute_fft()
    
    # Reconstruct: Get magnitude and phase, then IFFT
    magnitude = processor.get_magnitude()
    phase = processor.get_phase()
    
    # Reconstruct FFT from magnitude and phase
    reconstructed_fft = magnitude * np.exp(1j * phase)
    
    # IFFT to get back spatial image
    reconstructed_image = np.real(np.fft.ifft2(np.fft.ifftshift(reconstructed_fft)))
    
    # Calculate error
    difference = np.abs(original_image - reconstructed_image)
    max_error = difference.max()
    mean_error = difference.mean()
    
    # Display
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    axes[0].imshow(original_image, cmap='gray')
    axes[0].set_title('Original Image')
    axes[0].axis('off')
    
    axes[1].imshow(reconstructed_image, cmap='gray')
    axes[1].set_title('Reconstructed (FFT→IFFT)')
    axes[1].axis('off')
    
    axes[2].imshow(difference, cmap='hot')
    axes[2].set_title(f'Error Map\nMax: {max_error:.6f}')
    axes[2].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    print(f"\n📊 Reconstruction Quality:")
    print(f"   Max error: {max_error:.10f}")
    print(f"   Mean error: {mean_error:.10f}")
    print(f"   Relative error: {(max_error / original_image.max() * 100):.6f}%")
    
    # PASS/FAIL
    if max_error < 0.001:
        print(f"\n✅ PASS: Reconstruction is nearly perfect!")
    else:
        print(f"\n❌ FAIL: Reconstruction error too high!")
    
    return max_error < 0.001



def test_phase_dominance():
    """
    TEST: Swapping phases should swap image identities
    PASS CRITERIA: Mixed image looks like phase source, not magnitude source
    """
    print("\n" + "="*60)
    print("TEST 2: Phase Dominance (Structure vs Brightness)")
    print("="*60)
    
    # Load two DIFFERENT images
    proc1 = ImageProcessor()
    proc1.load_image('test_images/Steve_(Minecraft).png')
    proc1.convert_to_grayscale()
    proc1.resize_image((256, 256))
    proc1.compute_fft()
    
    proc2 = ImageProcessor()
    proc2.load_image('test_images/building.png')
    proc2.convert_to_grayscale()
    proc2.resize_image((256, 256))
    proc2.compute_fft()
    
    # Get components
    mag1 = proc1.get_magnitude()
    phase1 = proc1.get_phase()
    mag2 = proc2.get_magnitude()
    phase2 = proc2.get_phase()
    
    # Mix A: Magnitude from Image 1, Phase from Image 2
    mixed_fft_A = mag1 * np.exp(1j * phase2)
    output_A = np.real(np.fft.ifft2(np.fft.ifftshift(mixed_fft_A)))
    
    # Mix B: Magnitude from Image 2, Phase from Image 1
    mixed_fft_B = mag2 * np.exp(1j * phase1)
    output_B = np.real(np.fft.ifft2(np.fft.ifftshift(mixed_fft_B)))
    
    # Normalize for display
    output_A = (output_A - output_A.min()) / (output_A.max() - output_A.min()) * 255
    output_B = (output_B - output_B.min()) / (output_B.max() - output_B.min()) * 255
    
    # Display
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # Row 1
    axes[0, 0].imshow(proc1.image, cmap='gray')
    axes[0, 0].set_title('Image 1\n(Steve)')
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(proc2.image, cmap='gray')
    axes[0, 1].set_title('Image 2\n(Building)')
    axes[0, 1].axis('off')
    
    axes[0, 2].text(0.5, 0.5, 'QUESTION:\nWhich image does\neach output\nlook like?',
                     ha='center', va='center', fontsize=12, weight='bold')
    axes[0, 2].axis('off')
    
    # Row 2
    axes[1, 0].imshow(output_A, cmap='gray')
    axes[1, 0].set_title('Mix A:\nMag(Steve) + Phase(Building)')
    axes[1, 0].axis('off')
    
    axes[1, 1].imshow(output_B, cmap='gray')
    axes[1, 1].set_title('Mix B:\nMag(Building) + Phase(Steve)')
    axes[1, 1].axis('off')
    
    axes[1, 2].text(0.5, 0.5, 'ANSWER:\nMix A looks like Building\nMix B looks like Steve\n\n(Phase wins!)',
                     ha='center', va='center', fontsize=12, weight='bold', color='green')
    axes[1, 2].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    print("\n📊 Visual Inspection Required:")
    print("   Mix A should look like Image 2 (Building) ← Phase source")
    print("   Mix B should look like Image 1 (Steve) ← Phase source")
    print("\n✅ If yes → Phase dominance confirmed!")
    print("❌ If no → Implementation error!")
    
    response = input("\nDoes Mix A look like Building and Mix B look like Steve? (y/n): ")
    return response.lower() == 'y'



def test_frequency_regions():
    """
    TEST: Inner region should give blur, outer region should give edges
    PASS CRITERIA: 
    - Inner region: Low variance (smooth)
    - Outer region: High variance (edges)
    """
    print("\n" + "="*60)
    print("TEST 3: Frequency Region Filtering")
    print("="*60)
    
    from classes.fourier_mixer import FourierMixer
    
    # Load image
    processors = []
    for i in range(4):
        proc = ImageProcessor()
        proc.load_image('test_images/building.png')  # Use building (has clear edges)
        proc.convert_to_grayscale()
        proc.resize_image((256, 256))
        proc.compute_fft()
        processors.append(proc)
    
    mixer = FourierMixer(processors)
    mixer.set_mode('magnitude_phase')
    mixer.set_weights('magnitude', [1.0, 0, 0, 0])
    mixer.set_weights('phase', [1.0, 0, 0, 0])
    
    # Test 1: Inner region (low frequencies)
    mixer.set_region(size=0.3, region_type='inner', enabled=True)
    output_inner = mixer.compute_ifft(report_progress=False)
    
    # Test 2: Outer region (high frequencies)
    mixer.set_region(size=0.3, region_type='outer', enabled=True)
    output_outer = mixer.compute_ifft(report_progress=False)
    
    # Test 3: No filter (all frequencies)
    mixer.set_region(size=0.3, region_type='inner', enabled=False)
    output_full = mixer.compute_ifft(report_progress=False)
    
    # Calculate variance (measure of detail/sharpness)
    # Higher variance = more edges/details
    variance_inner = np.var(output_inner)
    variance_outer = np.var(output_outer)
    variance_full = np.var(output_full)
    
    # Calculate edge strength using Sobel filter
    from scipy import ndimage
    
    def edge_strength(image):
        sobel_x = ndimage.sobel(image, axis=0)
        sobel_y = ndimage.sobel(image, axis=1)
        return np.mean(np.sqrt(sobel_x**2 + sobel_y**2))
    
    edges_inner = edge_strength(output_inner)
    edges_outer = edge_strength(output_outer)
    edges_full = edge_strength(output_full)
    
    # Display
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    axes[0, 0].imshow(output_inner, cmap='gray')
    axes[0, 0].set_title('Inner Region\n(Low Frequencies)')
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(output_outer, cmap='gray')
    axes[0, 1].set_title('Outer Region\n(High Frequencies)')
    axes[0, 1].axis('off')
    
    axes[0, 2].imshow(output_full, cmap='gray')
    axes[0, 2].set_title('No Filter\n(All Frequencies)')
    axes[0, 2].axis('off')
    
    # Show frequency masks
    mixer.set_region(size=0.3, region_type='inner', enabled=True)
    mask_inner = mixer.get_mask_visualization()
    
    mixer.set_region(size=0.3, region_type='outer', enabled=True)
    mask_outer = mixer.get_mask_visualization()
    
    axes[1, 0].imshow(mask_inner, cmap='gray')
    axes[1, 0].set_title('Inner Mask')
    axes[1, 0].axis('off')
    
    axes[1, 1].imshow(mask_outer, cmap='gray')
    axes[1, 1].set_title('Outer Mask')
    axes[1, 1].axis('off')
    
    axes[1, 2].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    print(f"\n📊 Quantitative Analysis:")
    print(f"   Variance (detail measure):")
    print(f"      Inner: {variance_inner:.2f} (should be LOW)")
    print(f"      Outer: {variance_outer:.2f} (should be HIGH)")
    print(f"      Full:  {variance_full:.2f}")
    print(f"\n   Edge Strength:")
    print(f"      Inner: {edges_inner:.2f} (should be LOW)")
    print(f"      Outer: {edges_outer:.2f} (should be HIGH)")
    print(f"      Full:  {edges_full:.2f}")
    
    # PASS/FAIL criteria
    inner_is_blurry = edges_inner < edges_full * 0.5  # Inner has <50% edge strength
    outer_is_sharp = edges_outer > edges_inner * 2    # Outer has >2x edge strength
    
    if inner_is_blurry and outer_is_sharp:
        print(f"\n✅ PASS: Region filtering works correctly!")
        print(f"   - Inner region is blurry (low edge strength)")
        print(f"   - Outer region is sharp (high edge strength)")
        return True
    else:
        print(f"\n❌ FAIL: Region filtering not working correctly!")
        return False




def test_weighted_mixing():
    """
    TEST: Weights should proportionally control image contributions
    PASS CRITERIA: Output should be closer to higher-weighted input
    """
    print("\n" + "="*60)
    print("TEST 4: Weighted Mixing")
    print("="*60)
    
    from classes.fourier_mixer import FourierMixer
    
    # Load two different images
    proc1 = ImageProcessor()
    proc1.load_image('test_images/Steve_(Minecraft).png')
    proc1.convert_to_grayscale()
    proc1.resize_image((256, 256))
    proc1.compute_fft()
    
    proc2 = ImageProcessor()
    proc2.load_image('test_images/building.png')
    proc2.convert_to_grayscale()
    proc2.resize_image((256, 256))
    proc2.compute_fft()
    
    # Create 4 processors (use same two images twice)
    processors = [proc1, proc2, proc1, proc2]
    mixer = FourierMixer(processors)
    mixer.set_mode('magnitude_phase')
    
    # Test A: 100% from Image 1
    mixer.set_weights('magnitude', [1.0, 0, 0, 0])
    mixer.set_weights('phase', [1.0, 0, 0, 0])
    output_100_img1 = mixer.compute_ifft(report_progress=False)
    
    # Test B: 50% Image 1 + 50% Image 2
    mixer.set_weights('magnitude', [0.5, 0.5, 0, 0])
    mixer.set_weights('phase', [0.5, 0.5, 0, 0])
    output_50_50 = mixer.compute_ifft(report_progress=False)
    
    # Test C: 100% from Image 2
    mixer.set_weights('magnitude', [0, 1.0, 0, 0])
    mixer.set_weights('phase', [0, 1.0, 0, 0])
    output_100_img2 = mixer.compute_ifft(report_progress=False)
    
    # Calculate similarity (correlation coefficient)
    def similarity(img1, img2):
        return np.corrcoef(img1.flatten(), img2.flatten())[0, 1]
    
    sim_A_to_img1 = similarity(output_100_img1, proc1.image)
    sim_A_to_img2 = similarity(output_100_img1, proc2.image)
    
    sim_B_to_img1 = similarity(output_50_50, proc1.image)
    sim_B_to_img2 = similarity(output_50_50, proc2.image)
    
    sim_C_to_img1 = similarity(output_100_img2, proc1.image)
    sim_C_to_img2 = similarity(output_100_img2, proc2.image)
    
    # Display
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    axes[0, 0].imshow(proc1.image, cmap='gray')
    axes[0, 0].set_title('Image 1 (Steve)')
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(proc2.image, cmap='gray')
    axes[0, 1].set_title('Image 2 (Building)')
    axes[0, 1].axis('off')
    
    axes[0, 2].axis('off')
    
    axes[1, 0].imshow(output_100_img1, cmap='gray')
    axes[1, 0].set_title(f'100% Image 1\nSim to Img1: {sim_A_to_img1:.3f}')
    axes[1, 0].axis('off')
    
    axes[1, 1].imshow(output_50_50, cmap='gray')
    axes[1, 1].set_title(f'50% Each\nSim to Img1: {sim_B_to_img1:.3f}\nSim to Img2: {sim_B_to_img2:.3f}')
    axes[1, 1].axis('off')
    
    axes[1, 2].imshow(output_100_img2, cmap='gray')
    axes[1, 2].set_title(f'100% Image 2\nSim to Img2: {sim_C_to_img2:.3f}')
    axes[1, 2].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    print(f"\n📊 Similarity Analysis:")
    print(f"   100% Image 1: Similarity to Img1 = {sim_A_to_img1:.4f} (should be HIGH)")
    print(f"   100% Image 1: Similarity to Img2 = {sim_A_to_img2:.4f} (should be LOW)")
    print(f"\n   50%-50%: Similarity to Img1 = {sim_B_to_img1:.4f} (should be MEDIUM)")
    print(f"   50%-50%: Similarity to Img2 = {sim_B_to_img2:.4f} (should be MEDIUM)")
    print(f"\n   100% Image 2: Similarity to Img1 = {sim_C_to_img1:.4f} (should be LOW)")
    print(f"   100% Image 2: Similarity to Img2 = {sim_C_to_img2:.4f} (should be HIGH)")
    
    # PASS/FAIL
    test_A = sim_A_to_img1 > 0.9  # 100% Img1 should be very similar to Img1
    test_C = sim_C_to_img2 > 0.9  # 100% Img2 should be very similar to Img2
    test_B = (0.5 < sim_B_to_img1 < 0.9) and (0.5 < sim_B_to_img2 < 0.9)  # 50-50 should be intermediate
    
    if test_A and test_C and test_B:
        print(f"\n✅ PASS: Weighted mixing works correctly!")
        return True
    else:
        print(f"\n❌ FAIL: Weights not controlling contribution properly!")
        return False




def test_parsevals_theorem():
    """
    TEST: Parseval's Theorem - Energy should be conserved
    ∑|f(x,y)|² = ∑|F(u,v)|²
    PASS CRITERIA: Ratio ≈ 1.0 (within 1%)
    """
    print("\n" + "="*60)
    print("TEST 5: Parseval's Theorem (Energy Conservation)")
    print("="*60)
    
    processor = ImageProcessor()
    processor.load_image('test_images/Steve_(Minecraft).png')
    processor.convert_to_grayscale()
    processor.resize_image((256, 256))
    processor.compute_fft()
    
    # Energy in spatial domain
    spatial_energy = np.sum(np.abs(processor.image)**2)
    
    # Energy in frequency domain
    frequency_energy = np.sum(np.abs(processor.fft_result)**2)
    
    # According to Parseval's theorem, these should be equal (up to scaling)
    # FFT introduces a scaling factor of N (image size)
    N = processor.image.size
    scaled_frequency_energy = frequency_energy / N
    
    ratio = scaled_frequency_energy / spatial_energy
    
    print(f"\n📊 Energy Analysis:")
    print(f"   Spatial domain energy:    {spatial_energy:.2f}")
    print(f"   Frequency domain energy:  {frequency_energy:.2f}")
    print(f"   Scaled frequency energy:  {scaled_frequency_energy:.2f}")
    print(f"   Ratio (should be ≈1.0):   {ratio:.6f}")
    print(f"   Difference from 1.0:      {abs(1.0 - ratio)*100:.4f}%")
    
    # PASS/FAIL
    if 0.99 < ratio < 1.01:  # Within 1%
        print(f"\n✅ PASS: Energy is conserved (Parseval's theorem holds)!")
        print(f"   This confirms FFT implementation is mathematically correct.")
        return True
    else:
        print(f"\n❌ FAIL: Energy not conserved - FFT implementation error!")
        return False



# File: tests/test_verification.py

def run_all_verification_tests():
    """Run all verification tests and generate report."""
    print("\n" + "="*70)
    print("COMPREHENSIVE VERIFICATION TEST SUITE")
    print("="*70)
    
    results = {}
    
    # Test 1: Perfect Reconstruction
    results['reconstruction'] = test_perfect_reconstruction()
    input("\nPress Enter to continue to next test...")
    
    # Test 2: Phase Dominance
    results['phase_dominance'] = test_phase_dominance()
    input("\nPress Enter to continue to next test...")
    
    # Test 3: Frequency Regions
    results['frequency_regions'] = test_frequency_regions()
    input("\nPress Enter to continue to next test...")
    
    # Test 4: Weighted Mixing
    results['weighted_mixing'] = test_weighted_mixing()
    input("\nPress Enter to continue to next test...")
    
    # Test 5: Parseval's Theorem
    results['parsevals_theorem'] = test_parsevals_theorem()
    
    # Final Report
    print("\n" + "="*70)
    print("FINAL VERIFICATION REPORT")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n{'='*70}")
    print(f"OVERALL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"{'='*70}\n")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Implementation is mathematically correct!")
    else:
        print("⚠️  Some tests failed. Review implementation.")
    
    return passed == total


if __name__ == "__main__":
    run_all_verification_tests()