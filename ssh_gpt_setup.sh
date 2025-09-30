#!/bin/bash

# SSH GPU Setup for GPT-OSS
echo "=== SSH GPU Setup for GPT-OSS ==="

# Create SSH authorized keys if not exists
mkdir -p ~/.ssh
touch ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

echo "SSH keys directory: ~/.ssh/"
echo "Authorized keys: ~/.ssh/authorized_keys"
echo ""

# Create SSH environment setup
cat > ~/.ssh/gpu_env.sh << 'EOF'
#!/bin/bash
# GPU Environment for SSH sessions
export OLLAMA_NUM_GPU=999
export OLLAMA_GPU_OVERHEAD=0
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_MAX_QUEUE=1
export MTL_SHADER_VALIDATION=0
export PATH="/usr/local/bin:$PATH"

echo "🖥️  GPU Environment Loaded"
echo "   GPU: Intel Iris Plus Graphics 640"
echo "   Available models:"
ollama list
echo ""
echo "Commands:"
echo "  gpt-oss           - Run GPT-OSS model"
echo "  gpt-oss-test      - Quick test"
echo "  gpu-status        - Check GPU status"
echo ""

# Aliases for convenience
alias gpt-oss='cd /Users/gagan/Desktop/gagan_projects/terminal_2 && ./run_gpt_oss_fixed.sh --chat'
alias gpt-oss-test='cd /Users/gagan/Desktop/gagan_projects/terminal_2 && ./run_gpt_oss_fixed.sh --test'
alias gpu-status='ollama ps && echo "GPU: Intel Iris Plus Graphics 640 (1536MB)"'
EOF

chmod +x ~/.ssh/gpu_env.sh

# Update SSH config
echo "# GPU-enabled SSH config" >> ~/.ssh/config
echo "AcceptEnv OLLAMA_*" >> ~/.ssh/config
echo "AcceptEnv MTL_*" >> ~/.ssh/config

# Create connection script for clients
cat > /Users/gagan/Desktop/gagan_projects/terminal_2/connect_ssh_gpu.sh << 'EOF'
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
EOF

chmod +x /Users/gagan/Desktop/gagan_projects/terminal_2/connect_ssh_gpu.sh

echo "✅ SSH GPU setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. From client machine, copy your public key:"
echo "   ssh-copy-id root@192.168.2.67"
echo ""
echo "2. Connect with GPU access:"
echo "   ssh -t root@192.168.2.67 'source ~/.ssh/gpu_env.sh && bash'"
echo ""
echo "3. Or use the connection script:"
echo "   ./connect_ssh_gpu.sh"
echo ""
echo "4. Once connected, test GPT-OSS:"
echo "   gpt-oss-test"
echo "   gpt-oss"