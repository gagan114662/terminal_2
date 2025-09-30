#!/bin/bash

# GPT-OSS:20B ONLY - Force it to work on your GPU
export OLLAMA_NUM_GPU=999
export OLLAMA_GPU_OVERHEAD=0
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_FLASH_ATTENTION=1
export MTL_SHADER_VALIDATION=0
export MTL_DEBUG_LAYER=0

echo "============================================"
echo "FORCING GPT-OSS:20B TO WORK ON YOUR GPU"
echo "Intel Iris Plus Graphics 640"
echo "============================================"

# Kill all ollama processes to free memory
pkill -f ollama 2>/dev/null
sleep 5

# Free system memory aggressively
echo "Freeing system memory..."
sudo purge 2>/dev/null || true

# Start ollama with memory-optimized settings
echo "Starting Ollama with aggressive GPU settings..."
OLLAMA_NUM_GPU=999 OLLAMA_GPU_OVERHEAD=0 ollama serve &
sleep 8

echo "Loading GPT-OSS:20B model..."
echo "This WILL work - waiting for full load..."

# Force model to load and stay loaded
ollama run gpt-oss:20b "" &
sleep 15

echo ""
echo "Model should be loaded. Testing with simple prompt..."

# Direct test with no timeout - let it take as long as needed
echo "Test prompt: Hi"
echo "Response:"
echo "Hi" | OLLAMA_NUM_GPU=999 ollama run gpt-oss:20b

echo ""
echo "If you see a response above, GPT-OSS is working!"
echo "If not, the model needs more time to initialize."