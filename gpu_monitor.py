#!/usr/bin/env python3
import subprocess
import time
import sys

def monitor_gpu():
    """Monitor GPU usage during AI inference"""
    print("GPU Monitor - Intel Iris Plus Graphics 640")
    print("Press Ctrl+C to stop")
    print("-" * 50)

    try:
        while True:
            # Check ollama processes
            result = subprocess.run(['ollama', 'ps'],
                                 capture_output=True, text=True)

            if result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:  # Has models loaded
                    print(f"[{time.strftime('%H:%M:%S')}] Active models:")
                    for line in lines[1:]:
                        if line.strip():
                            print(f"  {line}")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] No models loaded")

            # Check system resources
            vm_result = subprocess.run(['vm_stat'],
                                     capture_output=True, text=True)
            for line in vm_result.stdout.split('\n'):
                if 'Pages free:' in line:
                    free_pages = int(line.split(':')[1].strip().replace('.', ''))
                    free_mb = (free_pages * 4096) // (1024 * 1024)
                    print(f"[{time.strftime('%H:%M:%S')}] Free Memory: {free_mb} MB")
                    break

            time.sleep(5)

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
    except Exception as e:
        print(f"Monitor error: {e}")

if __name__ == "__main__":
    monitor_gpu()
