#!/usr/bin/env python3
import subprocess
import platform
import sys

def get_gpu_info():
    """Get GPU information on macOS using system_profiler"""
    print("=" * 60)
    print("GPU INFORMATION ON YOUR SYSTEM")
    print("=" * 60)

    # Get basic system info
    print(f"\nSystem: {platform.system()}")
    print(f"Machine: {platform.machine()}")
    print(f"Python Version: {sys.version}")

    # Get GPU info using system_profiler
    try:
        result = subprocess.run(
            ['system_profiler', 'SPDisplaysDataType'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            lines = result.stdout.split('\n')
            gpu_info = []
            current_gpu = {}

            for line in lines:
                line = line.strip()

                if 'Chipset Model:' in line:
                    if current_gpu:
                        gpu_info.append(current_gpu)
                    current_gpu = {'name': line.split(':')[1].strip()}
                elif 'Vendor:' in line and current_gpu:
                    current_gpu['vendor'] = line.split(':')[1].strip()
                elif 'VRAM' in line and current_gpu:
                    current_gpu['vram'] = line.split(':')[1].strip()
                elif 'Metal Support:' in line and current_gpu:
                    current_gpu['metal'] = line.split(':')[1].strip()
                elif 'Device ID:' in line and current_gpu:
                    current_gpu['device_id'] = line.split(':')[1].strip()

            if current_gpu:
                gpu_info.append(current_gpu)

            print("\nDetected GPUs:")
            for i, gpu in enumerate(gpu_info, 1):
                print(f"\nGPU {i}:")
                print(f"  Name: {gpu.get('name', 'Unknown')}")
                print(f"  Vendor: {gpu.get('vendor', 'Unknown')}")
                print(f"  VRAM: {gpu.get('vram', 'Unknown')}")
                print(f"  Metal Support: {gpu.get('metal', 'Unknown')}")
                print(f"  Device ID: {gpu.get('device_id', 'Unknown')}")
        else:
            print("Could not retrieve GPU information")

    except Exception as e:
        print(f"Error getting GPU info: {e}")

    # Check for Metal support
    print("\n" + "=" * 60)
    print("METAL FRAMEWORK SUPPORT")
    print("=" * 60)

    try:
        # Check if Metal framework is available
        result = subprocess.run(
            ['xcrun', '--sdk', 'macosx', '--show-sdk-version'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"macOS SDK Version: {result.stdout.strip()}")
            print("✓ Metal framework is available on this system")
        else:
            print("✗ Could not verify Metal framework availability")
    except:
        print("✗ Xcode Command Line Tools may not be installed")

    # OpenCL support check
    print("\n" + "=" * 60)
    print("OPENCL SUPPORT")
    print("=" * 60)

    try:
        result = subprocess.run(
            ['clinfo'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            # Parse basic OpenCL info
            for line in result.stdout.split('\n'):
                if 'Platform Name' in line or 'Device Name' in line:
                    print(line.strip())
        else:
            print("OpenCL info tool (clinfo) not installed")
            print("To install: brew install clinfo")
    except FileNotFoundError:
        print("OpenCL info tool (clinfo) not installed")
        print("To install: brew install clinfo")

    print("\n" + "=" * 60)
    print("GPU ACCESS METHODS AVAILABLE ON macOS:")
    print("=" * 60)
    print("""
1. Metal Performance Shaders (MPS) - Apple's GPU framework
   - Best for: Machine learning, image processing, scientific computing
   - Supported by: PyTorch (with MPS backend), TensorFlow-Metal

2. OpenCL - Cross-platform GPU computing
   - Best for: General purpose GPU computing
   - Status: Deprecated by Apple but still available

3. Core ML - Apple's machine learning framework
   - Best for: Deploying trained models on Apple devices
   - Optimized for Apple Silicon and Intel GPUs

4. Accelerate Framework - CPU/GPU vectorized computations
   - Best for: Linear algebra, signal processing
   - Automatically uses GPU when beneficial
    """)

    print("\n" + "=" * 60)
    print("RECOMMENDED NEXT STEPS:")
    print("=" * 60)
    print("""
To use your Intel Iris Plus Graphics 640 GPU:

1. For Machine Learning (PyTorch):
   # Use Python 3.11 or earlier (3.13 not yet supported)
   brew install python@3.11
   python3.11 -m venv ml_env
   source ml_env/bin/activate
   pip install torch torchvision torchaudio

2. For TensorFlow with Metal:
   pip install tensorflow-metal (requires tensorflow-macos)

3. For General GPU Computing:
   brew install pocl  # OpenCL implementation
   pip install pyopencl

4. For Image Processing:
   pip install opencv-python
   pip install scikit-image
    """)

if __name__ == "__main__":
    get_gpu_info()