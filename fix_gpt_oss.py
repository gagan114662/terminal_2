#!/usr/bin/env python3
import subprocess
import json
import os
import sys
import time

def check_system_resources():
    """Check system memory and GPU resources"""
    print("=== SYSTEM RESOURCE CHECK ===")

    # Check memory
    try:
        result = subprocess.run(['vm_stat'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        free_pages = 0
        for line in lines:
            if 'Pages free:' in line:
                free_pages = int(line.split(':')[1].strip().replace('.', ''))
                break

        free_mb = (free_pages * 4096) // (1024 * 1024)
        print(f"Free Memory: ~{free_mb} MB")

        if free_mb < 4000:  # Less than 4GB free
            print("⚠️  WARNING: Low memory for 20B model")
            return False
        else:
            print("✓ Sufficient memory available")
            return True

    except Exception as e:
        print(f"Could not check memory: {e}")
        return False

def create_optimized_modelfile():
    """Create optimized Modelfile for GPT-OSS"""
    print("\n=== CREATING OPTIMIZED MODELFILE ===")

    modelfile_content = '''# Optimized GPT-OSS Modelfile for Intel GPU
FROM gpt-oss:20b

# GPU and Memory Optimizations
PARAMETER num_ctx 2048
PARAMETER num_batch 1
PARAMETER num_gqa 1
PARAMETER num_gpu 999
PARAMETER num_thread 4

# Performance tuning for Intel GPU
PARAMETER temperature 0.7
PARAMETER top_k 40
PARAMETER top_p 0.9
PARAMETER repeat_last_n 64
PARAMETER repeat_penalty 1.1

# Memory management
PARAMETER mmap true
PARAMETER mlock false
PARAMETER numa false

TEMPLATE """<|start|>system<|message|>You are ChatGPT, a large language model trained by OpenAI.
Knowledge cutoff: 2024-06
Current date: {{ currentDate }}
<|end|>
{{- range .Messages }}
  {{- if eq .Role "user" }}
<|start|>{{ .Role }}<|message|>{{ .Content }}<|end|>
  {{- else if eq .Role "assistant" }}
<|start|>assistant<|message|>{{ .Content }}<|end|>
  {{- end }}
{{- end }}
<|start|>assistant<|message|>"""
'''

    with open('/Users/gagan/Desktop/gagan_projects/terminal_2/Modelfile.gpt-oss-optimized', 'w') as f:
        f.write(modelfile_content)

    print("✓ Created optimized Modelfile")
    return True

def build_optimized_model():
    """Build optimized version of GPT-OSS model"""
    print("\n=== BUILDING OPTIMIZED MODEL ===")

    try:
        # Build the optimized model
        result = subprocess.run([
            'ollama', 'create', 'gpt-oss-fast',
            '-f', '/Users/gagan/Desktop/gagan_projects/terminal_2/Modelfile.gpt-oss-optimized'
        ], capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print("✓ Built optimized gpt-oss-fast model")
            return True
        else:
            print(f"✗ Failed to build model: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("✗ Model building timed out")
        return False
    except Exception as e:
        print(f"✗ Error building model: {e}")
        return False

def configure_ollama_gpu():
    """Configure Ollama for optimal GPU usage"""
    print("\n=== CONFIGURING OLLAMA FOR GPU ===")

    # Create ollama config directory
    config_dir = os.path.expanduser('~/.ollama')
    os.makedirs(config_dir, exist_ok=True)

    # GPU configuration
    gpu_config = {
        "OLLAMA_NUM_GPU": "999",
        "OLLAMA_GPU_OVERHEAD": "0",
        "OLLAMA_MAX_LOADED_MODELS": "1",
        "OLLAMA_MAX_QUEUE": "1",
        "OLLAMA_NUM_PARALLEL": "1",
        "OLLAMA_FLASH_ATTENTION": "1",
        "MTL_SHADER_VALIDATION": "0"
    }

    # Write environment file
    env_file = os.path.join(config_dir, 'env')
    with open(env_file, 'w') as f:
        for key, value in gpu_config.items():
            f.write(f"{key}={value}\n")

    print("✓ Created Ollama GPU configuration")

    # Also set in current environment
    for key, value in gpu_config.items():
        os.environ[key] = value

    return True

def test_optimized_model():
    """Test the optimized GPT-OSS model"""
    print("\n=== TESTING OPTIMIZED MODEL ===")

    test_prompt = "Hi, respond with just 'Hello!' to test you're working."

    try:
        print("Testing gpt-oss-fast model...")
        start_time = time.time()

        result = subprocess.run([
            'ollama', 'run', 'gpt-oss-fast', test_prompt
        ], capture_output=True, text=True, timeout=60,
        env={**os.environ, 'OLLAMA_NUM_GPU': '999'})

        elapsed = time.time() - start_time

        if result.returncode == 0 and result.stdout.strip():
            print(f"✓ Model responded in {elapsed:.1f}s:")
            print(f"Response: {result.stdout.strip()}")
            return True
        else:
            print(f"✗ Model test failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("✗ Model test timed out")
        return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False

def setup_ssh_gpu_access():
    """Set up SSH access with GPU forwarding"""
    print("\n=== SETTING UP SSH GPU ACCESS ===")

    # Create SSH wrapper script
    ssh_script = '''#!/bin/bash

# SSH GPU Access Script for GPT-OSS
export OLLAMA_NUM_GPU=999
export OLLAMA_GPU_OVERHEAD=0
export MTL_SHADER_VALIDATION=0
export OLLAMA_MAX_LOADED_MODELS=1

echo "=== GPU-Enabled SSH Session ==="
echo "GPU: Intel Iris Plus Graphics 640"
echo "Models available:"
ollama list

echo ""
echo "To use GPT-OSS optimized:"
echo "  ollama run gpt-oss-fast"
echo ""
echo "To use original (may be slow):"
echo "  ollama run gpt-oss:20b"
echo ""

# Start interactive shell with GPU env
exec "$@"
'''

    script_path = '/Users/gagan/Desktop/gagan_projects/terminal_2/ssh_gpu.sh'
    with open(script_path, 'w') as f:
        f.write(ssh_script)

    os.chmod(script_path, 0o755)

    print("✓ Created SSH GPU wrapper script")
    print(f"  Location: {script_path}")

    # Create convenient aliases
    aliases_content = '''
# GPU-accelerated AI aliases
alias gpt-fast="OLLAMA_NUM_GPU=999 ollama run gpt-oss-fast"
alias gpt-original="OLLAMA_NUM_GPU=999 ollama run gpt-oss:20b"
alias gpu-status="ollama ps && echo 'GPU: Intel Iris Plus Graphics 640'"
'''

    aliases_path = '/Users/gagan/Desktop/gagan_projects/terminal_2/gpu_aliases.sh'
    with open(aliases_path, 'w') as f:
        f.write(aliases_content)

    print(f"✓ Created GPU aliases file: {aliases_path}")
    return True

def create_gpu_monitor():
    """Create GPU monitoring script"""
    print("\n=== CREATING GPU MONITOR ===")

    monitor_script = '''#!/usr/bin/env python3
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
                lines = result.stdout.strip().split('\\n')
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
            for line in vm_result.stdout.split('\\n'):
                if 'Pages free:' in line:
                    free_pages = int(line.split(':')[1].strip().replace('.', ''))
                    free_mb = (free_pages * 4096) // (1024 * 1024)
                    print(f"[{time.strftime('%H:%M:%S')}] Free Memory: {free_mb} MB")
                    break

            time.sleep(5)

    except KeyboardInterrupt:
        print("\\nMonitoring stopped.")
    except Exception as e:
        print(f"Monitor error: {e}")

if __name__ == "__main__":
    monitor_gpu()
'''

    monitor_path = '/Users/gagan/Desktop/gagan_projects/terminal_2/gpu_monitor.py'
    with open(monitor_path, 'w') as f:
        f.write(monitor_script)

    os.chmod(monitor_path, 0o755)
    print(f"✓ Created GPU monitor: {monitor_path}")
    return True

def main():
    print("GPT-OSS GPU OPTIMIZATION TOOL")
    print("=" * 50)

    # Step 1: Check system resources
    if not check_system_resources():
        print("\n⚠️  Your system may struggle with the 20B model.")
        print("   Proceeding with optimization anyway...")

    # Step 2: Configure Ollama for GPU
    configure_ollama_gpu()

    # Step 3: Create optimized model
    create_optimized_modelfile()
    if not build_optimized_model():
        print("\n✗ Could not build optimized model")
        print("  Continuing with original model...")

    # Step 4: Set up SSH access
    setup_ssh_gpu_access()

    # Step 5: Create monitoring tools
    create_gpu_monitor()

    # Step 6: Test the setup
    print("\n=== TESTING SETUP ===")
    test_optimized_model()

    print("\n" + "=" * 50)
    print("SETUP COMPLETE!")
    print("=" * 50)
    print("""
Next steps:

1. SSH Usage:
   ssh root@192.168.2.67 'bash -c "source /Users/gagan/Desktop/gagan_projects/terminal_2/ssh_gpu.sh && bash"'

2. Local GPU aliases:
   source /Users/gagan/Desktop/gagan_projects/terminal_2/gpu_aliases.sh

3. Quick commands:
   gpt-fast          # Use optimized model
   gpt-original      # Use original 20B model
   gpu-status        # Check GPU status

4. Monitor GPU:
   python3 /Users/gagan/Desktop/gagan_projects/terminal_2/gpu_monitor.py

5. If models still hang, try:
   ollama serve --max-loaded-models 1 --max-queue 1
    """)

if __name__ == "__main__":
    main()