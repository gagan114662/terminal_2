#!/bin/bash

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
