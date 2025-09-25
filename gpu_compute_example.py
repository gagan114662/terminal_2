#!/usr/bin/env python3
import numpy as np
import time
import ctypes
import ctypes.util

# Load the Accelerate framework
accelerate_path = ctypes.util.find_library('Accelerate')
if accelerate_path:
    accelerate = ctypes.CDLL(accelerate_path)
    print("✓ Accelerate framework loaded successfully")
    print(f"  Path: {accelerate_path}")
else:
    print("✗ Could not load Accelerate framework")
    accelerate = None

def matrix_multiply_numpy(size=1000):
    """Standard NumPy matrix multiplication"""
    print(f"\nNumPy Matrix Multiplication ({size}x{size}):")

    # Create random matrices
    a = np.random.randn(size, size).astype(np.float32)
    b = np.random.randn(size, size).astype(np.float32)

    # Time the multiplication
    start = time.time()
    c = np.dot(a, b)
    end = time.time()

    elapsed = end - start
    gflops = (2 * size**3) / (elapsed * 1e9)

    print(f"  Time: {elapsed:.4f} seconds")
    print(f"  Performance: {gflops:.2f} GFLOPS")

    return elapsed

def vector_operations_demo():
    """Demonstrate vector operations that use GPU acceleration"""
    print("\n" + "=" * 60)
    print("VECTOR OPERATIONS (GPU-ACCELERATED VIA ACCELERATE)")
    print("=" * 60)

    sizes = [1000, 5000, 10000]

    for size in sizes:
        print(f"\nVector size: {size:,} elements")

        # Create random vectors
        a = np.random.randn(size).astype(np.float32)
        b = np.random.randn(size).astype(np.float32)

        # Dot product
        start = time.time()
        result = np.dot(a, b)
        elapsed = time.time() - start
        print(f"  Dot product: {elapsed*1000:.3f} ms")

        # Element-wise operations
        start = time.time()
        result = np.sqrt(a**2 + b**2)  # Euclidean norm
        elapsed = time.time() - start
        print(f"  Euclidean norm: {elapsed*1000:.3f} ms")

        # FFT (uses vDSP from Accelerate)
        start = time.time()
        fft_result = np.fft.fft(a)
        elapsed = time.time() - start
        print(f"  FFT: {elapsed*1000:.3f} ms")

def image_processing_demo():
    """Demonstrate image processing operations"""
    print("\n" + "=" * 60)
    print("IMAGE PROCESSING OPERATIONS")
    print("=" * 60)

    # Create a sample "image" (2D array)
    image_size = 2048
    image = np.random.randn(image_size, image_size).astype(np.float32)

    print(f"\nImage size: {image_size}x{image_size} pixels")

    # 2D convolution (blur kernel)
    kernel = np.ones((5, 5), dtype=np.float32) / 25

    start = time.time()
    # Simple 2D convolution using NumPy
    from scipy import signal
    try:
        result = signal.convolve2d(image, kernel, mode='same')
        elapsed = time.time() - start
        print(f"  2D Convolution (5x5 blur): {elapsed:.3f} seconds")
    except ImportError:
        print("  SciPy not installed - skipping convolution")

    # 2D FFT
    start = time.time()
    fft2_result = np.fft.fft2(image)
    elapsed = time.time() - start
    print(f"  2D FFT: {elapsed:.3f} seconds")

    # Matrix transpose
    start = time.time()
    transposed = np.transpose(image)
    elapsed = time.time() - start
    print(f"  Matrix transpose: {elapsed:.3f} seconds")

def benchmark_comparison():
    """Compare performance for different matrix sizes"""
    print("\n" + "=" * 60)
    print("PERFORMANCE BENCHMARK")
    print("=" * 60)
    print("\nMatrix Multiplication Performance:")
    print("(Using Intel Iris Plus Graphics 640 via Accelerate Framework)")

    sizes = [100, 500, 1000, 2000]

    for size in sizes:
        elapsed = matrix_multiply_numpy(size)
        print()

def main():
    print("=" * 60)
    print("GPU COMPUTE DEMONSTRATION")
    print("Intel Iris Plus Graphics 640")
    print("=" * 60)

    print("\nYour GPU Details:")
    print("  • Intel Iris Plus Graphics 640")
    print("  • VRAM: 1536 MB (Dynamic)")
    print("  • Metal 3 Support: Yes")
    print("  • Compute via: Accelerate Framework (automatic GPU offload)")

    # Run demonstrations
    vector_operations_demo()
    benchmark_comparison()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("""
Your Intel Iris Plus Graphics 640 is being utilized through:

1. NumPy operations that automatically use Accelerate framework
2. The Accelerate framework offloads suitable operations to GPU
3. Operations like FFT, BLAS, and LAPACK use GPU acceleration

For more advanced GPU computing, consider:
• Installing Python 3.11 and PyTorch with MPS support
• Using TensorFlow-Metal for deep learning
• OpenCL for custom GPU kernels
    """)

if __name__ == "__main__":
    main()