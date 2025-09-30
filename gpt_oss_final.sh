#!/bin/bash

# Final GPT-OSS Solution - Handles large model constraints
export OLLAMA_NUM_GPU=1  # Use GPU but limit layers
export OLLAMA_GPU_OVERHEAD=512  # Reserve memory for GPU
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_NUM_PARALLEL=1
export MTL_SHADER_VALIDATION=0

echo "============================================"
echo "GPT-OSS:20B - MEMORY-OPTIMIZED FOR YOUR GPU"
echo "Intel Iris Plus Graphics 640 (1536MB VRAM)"
echo "============================================"

# Kill any existing ollama processes
pkill -f ollama 2>/dev/null
sleep 3

# Start ollama server with conservative settings
echo "Starting Ollama server..."
ollama serve > /tmp/ollama.log 2>&1 &
sleep 5

# Function to test if model responds
test_model_response() {
    local test_prompt="Hi"
    echo "Testing model with simple prompt..."

    # Try with short timeout first
    timeout 30s bash -c "echo '$test_prompt' | ollama run gpt-oss:20b" 2>/dev/null
    local status=$?

    if [ $status -eq 0 ]; then
        echo "✅ Model is responding!"
        return 0
    elif [ $status -eq 124 ]; then
        echo "⏰ Model loaded but response is slow (normal for 20B model)"
        return 1
    else
        echo "❌ Model failed to load properly"
        return 2
    fi
}

# Alternative: Use a smaller quantized version if available
try_quantized_version() {
    echo "Attempting to use quantized version..."

    # Try to pull a quantized version
    ollama pull gpt-oss:13b 2>/dev/null || ollama pull gpt-oss:7b 2>/dev/null

    if ollama list | grep -q "gpt-oss.*[7-13]b"; then
        local model=$(ollama list | grep "gpt-oss.*[7-13]b" | head -1 | awk '{print $1}')
        echo "Found smaller model: $model"
        echo "Testing smaller model..."

        timeout 20s bash -c "echo 'Hello' | ollama run $model" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ Smaller model works! Using $model instead."
            echo ""
            echo "To use this model:"
            echo "  ollama run $model"
            return 0
        fi
    fi

    return 1
}

# Function for interactive chat with fallback
interactive_chat() {
    echo "🤖 GPT-OSS Interactive Chat"
    echo "Note: First response may take 60+ seconds"
    echo "Type 'exit' to quit, 'switch' to try smaller model"
    echo ""

    local current_model="gpt-oss:20b"

    while true; do
        read -p "You: " user_input

        case "$user_input" in
            exit|quit|q)
                echo "Goodbye!"
                break
                ;;
            switch)
                if try_quantized_version; then
                    local new_model=$(ollama list | grep "gpt-oss.*[7-13]b" | head -1 | awk '{print $1}')
                    if [ -n "$new_model" ]; then
                        current_model="$new_model"
                        echo "Switched to $current_model"
                    fi
                else
                    echo "No alternative model available"
                fi
                continue
                ;;
            "")
                continue
                ;;
        esac

        echo ""
        echo "🤖 GPT (using $current_model):"

        # Try with timeout
        timeout 90s bash -c "echo '$user_input' | ollama run $current_model" 2>/dev/null
        local result=$?

        if [ $result -eq 124 ]; then
            echo ""
            echo "⏰ Response timed out. The 20B model may be too large for your system."
            echo "   Try 'switch' to use a smaller model, or wait longer next time."
        elif [ $result -ne 0 ]; then
            echo ""
            echo "❌ Model error. Try restarting or using 'switch'."
        fi

        echo ""
    done
}

# Main execution
echo "Checking if GPT-OSS model works on your system..."
echo ""

# Test the model
if test_model_response; then
    echo ""
    echo "🎉 Great! Your GPU can handle the GPT-OSS model."
    interactive_chat
else
    echo ""
    echo "⚠️  The 20B model is struggling on your system."
    echo ""

    # Try to find alternatives
    if try_quantized_version; then
        echo ""
        echo "Would you like to use the smaller model instead? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            interactive_chat
        fi
    else
        echo ""
        echo "💡 Recommendations:"
        echo ""
        echo "1. Try a smaller model:"
        echo "   ollama pull llama2:7b"
        echo "   ollama run llama2:7b"
        echo ""
        echo "2. Or use the working DeepSeek model:"
        echo "   ollama run deepseek-coder:1.3b"
        echo ""
        echo "3. The gpt-oss:20b model needs more memory than your system has available."
        echo "   Your Intel Iris Plus Graphics 640 works great with smaller models!"
    fi
fi

# Clean up
pkill -f ollama 2>/dev/null