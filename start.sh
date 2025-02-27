#!/usr/bin/env bash

# Use libtcmalloc for better memory management
TCMALLOC="$(ldconfig -p | grep -Po "libtcmalloc.so.\d" | head -n 1)"
export LD_PRELOAD="${TCMALLOC}"

start_comfyui() {
    echo "test-comfy: Starting ComfyUI"
    # Add logging for startup
    python3 /comfyui/main.py --disable-auto-launch --disable-metadata --listen 2>&1 | tee comfyui.log &
    COMFY_PID=$!
    
    # Increase wait time and add better error checking
    for i in {1..30}; do
        if ! kill -0 $COMFY_PID 2>/dev/null; then
            echo "ComfyUI process died. Checking logs..."
            tail -n 50 comfyui.log
            exit 1
        fi
        
        # Check if service is responding
        if curl -s "http://127.0.0.1:8188/system_stats" >/dev/null; then
            echo "ComfyUI started successfully"
            break
        fi
        
        echo "Waiting for ComfyUI to start... ($i/30)"
        sleep 2
    done
}

# Serve the API and don't shutdown the container
if [ "$SERVE_API_LOCALLY" == "true" ]; then
    start_comfyui
    echo "test-comfy: Starting RunPod Handler"
    python3 -u handler.py --rp_serve_api --rp_api_host=0.0.0.0
else
    start_comfyui
    echo "test-comfy: Starting RunPod Handler"
    python3 -u handler.py
fi