import runpod
import json
import base64
import requests
import time
import os

# Constants
COMFY_HOST = "127.0.0.1:8188"
MAX_RETRIES = 30
RETRY_DELAY = 2
POLLING_INTERVAL = 1

def wait_for_comfy_ui():
    """
    Wait for ComfyUI server to be ready
    """
    for _ in range(MAX_RETRIES):
        try:
            response = requests.get(f"http://{COMFY_HOST}/system_stats")
            if response.status_code == 200:
                print("ComfyUI API is reachable")
                return True
        except requests.exceptions.ConnectionError:
            time.sleep(RETRY_DELAY)
    
    raise Exception("ComfyUI server failed to start after 60 seconds")

def load_workflow():
    """
    Load the GO_T2I_Workflow.json file
    """
    try:
        workflow_path = '/comfyui/GO_T2I_Workflow.json'
        with open(workflow_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        raise Exception(f"Failed to load workflow: {str(e)}")

def handler(event):
    """
    Handler that runs the GO_T2I_Workflow and returns the generated image as base64
    """
    try:
        # Wait for ComfyUI to be ready
        wait_for_comfy_ui()
        
        # Get the workflow
        workflow = load_workflow()
        
        # Get the prompt from input
        prompt = event["input"].get("prompt", "")
        
        # Update the text inputs in the workflow
        workflow["39"]["inputs"]["text"] = prompt  # Update BGED text input
        workflow["104"]["inputs"]["text"] = prompt  # Update MixlabApp text input
        
        # Queue the workflow
        api_url = f"http://{COMFY_HOST}/prompt"
        response = requests.post(api_url, json={"prompt": workflow})
        
        if response.status_code != 200:
            raise Exception(f"ComfyUI API request failed with status {response.status_code}")
            
        # Get the job ID from response
        job_id = response.json()['prompt_id']
        print(f"Queued workflow with ID {job_id}")
        
        # Poll for results
        while True:
            history_url = f"http://{COMFY_HOST}/history/{job_id}"
            history = requests.get(history_url).json()
            
            if job_id in history:
                if 'outputs' in history[job_id]:
                    # Get the output image path
                    output_images = history[job_id]['outputs']
                    if output_images and '113' in output_images:  # 113 is our PreviewImage node
                        image_path = output_images['113']['images'][0]['filename']
                        subfolder = output_images['113']['images'][0]['subfolder']
                        full_path = f"/comfyui/output/{subfolder}/{image_path}"
                        
                        # Read the image and convert to base64
                        with open(full_path, "rb") as img_file:
                            img_data = base64.b64encode(img_file.read()).decode()
                            
                        return {"base64_image": img_data}
                break
                
            time.sleep(POLLING_INTERVAL)
            
    except Exception as e:
        return {"error": str(e)}

# Start the serverless function
runpod.serverless.start({"handler": handler})