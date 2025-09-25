
# GPU-accelerated AI aliases
alias gpt-fast="OLLAMA_NUM_GPU=999 ollama run gpt-oss-fast"
alias gpt-original="OLLAMA_NUM_GPU=999 ollama run gpt-oss:20b"
alias gpu-status="ollama ps && echo 'GPU: Intel Iris Plus Graphics 640'"
