#!/bin/bash

# Enable GPU acceleration for gpt-oss model
export OLLAMA_NUM_GPU=999  # Use all GPU layers
export OLLAMA_GPU_OVERHEAD=0  # Minimize overhead
export MTL_SHADER_VALIDATION=0  # Disable Metal validation for speed

echo "============================================"
echo "GPT-OSS:20B with GPU Acceleration"
echo "GPU: Intel Iris Plus Graphics 640"
echo "============================================"

# Start ollama in background if not running
pgrep -x ollama > /dev/null || ollama serve &>/dev/null &
sleep 2

# Function to run gpt-oss
run_gpt() {
    local prompt="$1"
    echo "Prompt: $prompt"
    echo "--------------------------------------------"
    echo "$prompt" | ollama run gpt-oss:20b 2>/dev/null
    echo "--------------------------------------------"
}

# If argument provided, use it as prompt
if [ $# -gt 0 ]; then
    run_gpt "$*"
else
    # Interactive mode
    echo "Interactive mode. Type 'exit' to quit."
    echo ""
    while true; do
        read -p "You: " prompt
        if [ "$prompt" = "exit" ]; then
            break
        fi
        echo ""
        echo -n "GPT: "
        echo "$prompt" | ollama run gpt-oss:20b 2>/dev/null
        echo ""
    done
fi