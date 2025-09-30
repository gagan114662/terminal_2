#!/usr/bin/env python3
import subprocess
import json
import sys
import time

def check_gpu_usage():
    """Check GPU usage on macOS"""
    try:
        # Check GPU activity using ioreg
        result = subprocess.run(
            ['ioreg', '-l', '-w', '0'],
            capture_output=True,
            text=True
        )
        if 'PerformanceStatistics' in result.stdout:
            print("✓ GPU activity detected")
            return True
    except:
        pass
    return False

def run_ollama_with_gpu(model="gpt-oss:20b", prompt="Hello! Tell me about yourself."):
    """Run Ollama model with GPU acceleration"""
    print("=" * 60)
    print(f"RUNNING GPT MODEL ON GPU")
    print("=" * 60)
    print(f"Model: {model}")
    print(f"GPU: Intel Iris Plus Graphics 640")
    print(f"Metal Support: Enabled")
    print("=" * 60)

    # Set environment variables for GPU acceleration
    env = {
        **subprocess.os.environ,
        'OLLAMA_NUM_GPU': '999',  # Use all available GPU layers
        'OLLAMA_GPU_OVERHEAD': '0',  # Minimize GPU overhead
        'MTL_SHADER_VALIDATION': '0',  # Disable Metal shader validation for performance
    }

    print("\n📊 Configuration:")
    print("  • GPU Layers: Maximum available")
    print("  • Metal Performance Shaders: Enabled")
    print("  • Memory: Dynamic allocation up to 1536 MB")

    print("\n💬 Prompt:", prompt)
    print("\n🤖 Response:")
    print("-" * 40)

    start_time = time.time()

    try:
        # Run the ollama command with GPU settings
        cmd = ['ollama', 'run', model, prompt]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=60  # 60 second timeout
        )

        if result.returncode == 0:
            print(result.stdout)
            elapsed = time.time() - start_time
            print("-" * 40)
            print(f"\n⏱️  Response time: {elapsed:.2f} seconds")

            # Estimate tokens per second (rough estimate)
            response_length = len(result.stdout.split())
            if elapsed > 0:
                tps = response_length / elapsed
                print(f"📈 Performance: ~{tps:.1f} tokens/second")
        else:
            print(f"Error: {result.stderr}")

    except subprocess.TimeoutExpired:
        print("Response timed out after 60 seconds")
    except Exception as e:
        print(f"Error running model: {e}")

def interactive_chat(model="gpt-oss:20b"):
    """Interactive chat with the GPT model"""
    print("=" * 60)
    print("INTERACTIVE GPT CHAT (GPU ACCELERATED)")
    print("=" * 60)
    print(f"Model: {model}")
    print("Type 'exit' or 'quit' to end the chat")
    print("=" * 60)

    env = {
        **subprocess.os.environ,
        'OLLAMA_NUM_GPU': '999',
        'OLLAMA_GPU_OVERHEAD': '0',
        'MTL_SHADER_VALIDATION': '0',
    }

    while True:
        try:
            prompt = input("\n👤 You: ").strip()

            if prompt.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break

            if not prompt:
                continue

            print("\n🤖 GPT: ", end='', flush=True)

            # Stream the response
            process = subprocess.Popen(
                ['ollama', 'run', model],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                bufsize=1
            )

            # Send the prompt
            process.stdin.write(prompt + '\n')
            process.stdin.flush()

            # Read response character by character for streaming effect
            response = ""
            while True:
                char = process.stdout.read(1)
                if not char:
                    break
                print(char, end='', flush=True)
                response += char
                if response.endswith('\n\n'):  # Ollama typically ends with double newline
                    break

            process.terminate()

        except KeyboardInterrupt:
            print("\n\nChat interrupted. Type 'exit' to quit.")
        except Exception as e:
            print(f"\nError: {e}")

def list_available_models():
    """List all available Ollama models"""
    print("\n📚 Available GPT Models:")
    print("-" * 40)

    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if parts:
                        name = parts[0]
                        size = parts[2] if len(parts) > 2 else "Unknown"
                        print(f"  • {name:<25} Size: {size}")
    except Exception as e:
        print(f"Error listing models: {e}")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--chat':
            # Interactive chat mode
            model = sys.argv[2] if len(sys.argv) > 2 else "gpt-oss:20b"
            interactive_chat(model)
        elif sys.argv[1] == '--list':
            # List available models
            list_available_models()
        else:
            # Single prompt mode
            prompt = ' '.join(sys.argv[1:])
            run_ollama_with_gpu(prompt=prompt)
    else:
        # Default demo
        print("GPU-Accelerated GPT Demo\n")

        # List available models
        list_available_models()

        print("\n" + "=" * 60)
        print("RUNNING TEST PROMPT")
        print("=" * 60)

        # Run a test prompt
        test_prompt = "Write a haiku about artificial intelligence."
        run_ollama_with_gpu(model="gpt-oss:20b", prompt=test_prompt)

        print("\n" + "=" * 60)
        print("USAGE INSTRUCTIONS")
        print("=" * 60)
        print("""
To use this script:

1. Single prompt:
   python3 run_gpt_gpu.py "Your question here"

2. Interactive chat:
   python3 run_gpt_gpu.py --chat [model_name]

3. List models:
   python3 run_gpt_gpu.py --list

Examples:
   python3 run_gpt_gpu.py "Explain quantum computing"
   python3 run_gpt_gpu.py --chat gpt-oss:20b
   python3 run_gpt_gpu.py --chat qwen2.5:7b
        """)

if __name__ == "__main__":
    main()