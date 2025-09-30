#!/bin/bash

# Complete GPT-OSS Connection Script
# Works both locally and via SSH

SERVER_IP="192.168.2.67"
SERVER_USER="root"

echo "🤖 GPT-OSS Connection Options"
echo "============================="
echo ""
echo "1. Local GPT-OSS via OpenRouter API"
echo "2. SSH to server with GPT-OSS access"
echo "3. Test GPT-OSS quickly"
echo ""

read -p "Choose option (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting local GPT-OSS..."
        cd /Users/gagan/Desktop/gagan_projects/terminal_2
        python3 gpt_oss_openrouter.py --chat
        ;;
    2)
        echo ""
        echo "🔗 Connecting to SSH server with GPT-OSS access..."
        echo "Server: $SERVER_IP"
        echo ""
        ssh -t $SERVER_USER@$SERVER_IP "source /Users/gagan/Desktop/gagan_projects/terminal_2/ssh_gpt_openrouter.sh && bash"
        ;;
    3)
        echo ""
        echo "⚡ Quick GPT-OSS test..."
        cd /Users/gagan/Desktop/gagan_projects/terminal_2
        python3 gpt_oss_openrouter.py "Hi! Please confirm you're working and tell me what you are."
        ;;
    *)
        echo "Invalid option. Exiting."
        exit 1
        ;;
esac