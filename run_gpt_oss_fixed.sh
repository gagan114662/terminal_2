#!/bin/bash

# GPT-OSS with GPU optimization and memory management
export OLLAMA_NUM_GPU=999
export OLLAMA_GPU_OVERHEAD=0
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_MAX_QUEUE=1
export OLLAMA_NUM_PARALLEL=1
export MTL_SHADER_VALIDATION=0
export MTL_DEBUG_LAYER=0

echo "============================================"
echo "GPT-OSS:20B - OPTIMIZED FOR YOUR GPU"
echo "Intel Iris Plus Graphics 640 with 1536MB"
echo "============================================"

# Check if ollama server is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama server with GPU optimizations..."
    ollama serve --max-loaded-models 1 --max-queue 1 &>/dev/null &
    sleep 3
fi

# Free up memory before loading model
echo "Optimizing system memory..."
sudo purge 2>/dev/null || echo "Memory optimization attempted"

# Function to run GPT-OSS with timeout and retry
run_gpt_oss() {
    local prompt="$1"
    local timeout_duration=45

    echo "Loading GPT-OSS model (this may take 30-60 seconds)..."
    echo "Prompt: $prompt"
    echo "--------------------------------------------"

    # Use timeout to prevent hanging
    if command -v gtimeout >/dev/null 2>&1; then
        timeout_cmd="gtimeout"
    elif timeout --help >/dev/null 2>&1; then
        timeout_cmd="timeout"
    else
        timeout_cmd=""
    fi

    if [ -n "$timeout_cmd" ]; then
        echo "$prompt" | $timeout_cmd ${timeout_duration}s ollama run gpt-oss:20b 2>/dev/null
        local exit_code=$?

        if [ $exit_code -eq 124 ]; then
            echo "Response timed out after ${timeout_duration} seconds"
            echo "This is normal for first-time loading of large models"
        elif [ $exit_code -eq 0 ]; then
            echo ""
            echo "Success! Model is responding."
        else
            echo "Model error (code: $exit_code)"
        fi
    else
        # Fallback without timeout
        echo "$prompt" | ollama run gpt-oss:20b 2>/dev/null &
        local ollama_pid=$!

        # Wait for response or timeout
        local count=0
        while [ $count -lt $timeout_duration ] && kill -0 $ollama_pid 2>/dev/null; do
            sleep 1
            count=$((count + 1))
        done

        if kill -0 $ollama_pid 2>/dev/null; then
            echo "Stopping model (taking too long)..."
            kill $ollama_pid
            wait $ollama_pid 2>/dev/null
        fi
    fi

    echo "--------------------------------------------"
}

# Interactive mode function
interactive_mode() {
    echo "Interactive GPT-OSS Chat"
    echo "Type 'exit', 'quit', or 'q' to end"
    echo "Type 'restart' to reload the model"
    echo ""

    while true; do
        read -p "You: " user_input

        case "$user_input" in
            exit|quit|q)
                echo "Goodbye!"
                break
                ;;
            restart)
                echo "Restarting model..."
                killall ollama 2>/dev/null
                sleep 2
                ollama serve --max-loaded-models 1 --max-queue 1 &>/dev/null &
                sleep 3
                continue
                ;;
            "")
                continue
                ;;
        esac

        echo ""
        echo -n "GPT: "
        run_gpt_oss "$user_input"
        echo ""
    done
}

# Check command line arguments
if [ $# -eq 0 ]; then
    # No arguments - show usage and start interactive mode
    echo "Usage:"
    echo "  $0 \"your prompt here\"     # Single prompt"
    echo "  $0 --chat                  # Interactive mode"
    echo "  $0 --test                  # Quick test"
    echo ""
    echo "Starting interactive mode..."
    echo ""
    interactive_mode
elif [ "$1" = "--chat" ]; then
    interactive_mode
elif [ "$1" = "--test" ]; then
    run_gpt_oss "Say 'Hello! I am working.' to test the connection."
else
    # Single prompt mode
    run_gpt_oss "$*"
fi