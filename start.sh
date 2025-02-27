#!/usr/bin/env bash

# Use libtcmalloc for better memory management
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libtcmalloc_minimal.so.4

start_comfyui() {
    echo "test-comfy: Starting ComfyUI"
    cd /comfyui
    
    # Initialize ComfyUI first
    python3 main.py --quick-test-startup --disable-auto-launch --disable-metadata --listen &
    COMFY_PID=$!
    
    # Wait for process to start and check logs
    sleep 5
    if ! ps -p $COMFY_PID > /dev/null; then
        echo "ComfyUI failed to start. Checking logs..."
        cat comfyui.log
        exit 1
    fi
    
    # Wait for API to be available
    for i in {1..30}; do
        if curl -s "http://127.0.0.1:8188/system_stats" > /dev/null; then
            echo "ComfyUI API is available"
            break
        fi
        echo "Waiting for ComfyUI API... ($i/30)"
        sleep 2
    done
}

# Start services
start_comfyui

# Start the handler
echo "test-comfy: Starting RunPod Handler"
if [ "$SERVE_API_LOCALLY" == "true" ]; then
    python3 -u handler.py --rp_serve_api --rp_api_host=0.0.0.0
else
    python3 -u handler.py
fi

