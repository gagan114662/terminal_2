#!/bin/bash

# SSH Connection Script with GPU forwarding
SERVER_IP="192.168.2.67"
SERVER_USER="root"

echo "=== Connecting to GPU Server ==="
echo "Server: $SERVER_IP"
echo "User: $SERVER_USER"
echo ""

# SSH with GPU environment
ssh -t $SERVER_USER@$SERVER_IP "source ~/.ssh/gpu_env.sh && bash"
