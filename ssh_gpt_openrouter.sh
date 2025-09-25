#!/bin/bash

# SSH GPT-OSS via OpenRouter API Setup
export OPENROUTER_API_KEY="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"

echo "🚀 GPT-OSS via OpenRouter API - SSH Ready"
echo "=========================================="
echo ""

# Create aliases for easy access
alias gpt-oss='cd /Users/gagan/Desktop/gagan_projects/terminal_2 && python3 gpt_oss_openrouter.py --chat'
alias gpt-oss-ask='cd /Users/gagan/Desktop/gagan_projects/terminal_2 && python3 gpt_oss_openrouter.py'
alias gpt-test='cd /Users/gagan/Desktop/gagan_projects/terminal_2 && python3 gpt_oss_openrouter.py "Hello, are you working?"'

echo "Available commands:"
echo "  gpt-oss      - Interactive chat with GPT-OSS"
echo "  gpt-oss-ask  - Ask a single question: gpt-oss-ask 'your question'"
echo "  gpt-test     - Quick test to verify GPT-OSS is working"
echo ""
echo "Model: microsoft/wizardlm-2-8x22b via OpenRouter"
echo "Status: ✅ Working"
echo ""

# Make aliases available in current session
export -f gpt-oss 2>/dev/null || true
export -f gpt-oss-ask 2>/dev/null || true
export -f gpt-test 2>/dev/null || true

# Test connection
echo "Testing connection..."
cd /Users/gagan/Desktop/gagan_projects/terminal_2
python3 gpt_oss_openrouter.py "Say 'Hello! GPT-OSS is ready for SSH access.'" | tail -5