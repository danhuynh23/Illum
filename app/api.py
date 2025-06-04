import base64
import io
import tempfile
from pathlib import Path
from typing import Optional
import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from pydantic import BaseModel
import os
import sys
import subprocess
from PIL import Image

# Get the absolute path to the app directory
APP_DIR = Path(__file__).parent.absolute()
MUSETALK_DIR = APP_DIR / "musetalk"

# Add both app and musetalk directories to Python path
sys.path.extend([str(APP_DIR), str(MUSETALK_DIR)])

# Initialize FastAPI app
app = FastAPI(title="MuseTalk WebSocket API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input validation model
class LipSyncInput(BaseModel):
    image_base64: str
    audio_base64: str

def save_base64_to_file(base64_str: str, file_path: Path) -> None:
    """Save base64 string to a file."""
    data = base64.b64decode(base64_str)
    with open(file_path, 'wb') as f:
        f.write(data)

def get_base64_from_file(file_path: Path) -> str:
    """Read file and return as base64 string."""
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def preprocess_image(image_bytes):
    # Convert bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Calculate new dimensions (maintain aspect ratio and ensure even dimensions)
    max_dimension = 1024
    height, width = img.shape[:2]
    if height > width:
        new_height = max_dimension
        new_width = int(width * (max_dimension / height))
    else:
        new_width = max_dimension
        new_height = int(height * (max_dimension / width))
    
    # Ensure dimensions are even
    new_width = new_width - (new_width % 2)
    new_height = new_height - (new_height % 2)
    
    # Resize image
    resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
    
    # Convert back to bytes
    _, buffer = cv2.imencode('.jpg', resized)
    return buffer.tobytes()

def run_inference(image_path, audio_path):
    # Ensure output directory exists
    output_dir = APP_DIR / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    # Run the realtime inference script
    cmd = [
        sys.executable,  # Use the current Python interpreter
        str(MUSETALK_DIR / "scripts/realtime_inference.py"),
        "--version", "v15",
        "--inference_config", str(APP_DIR / "configs/inference/test.yaml"),
        "--result_dir", str(output_dir),
        "--fps", "25",
        "--batch_size", "2"
    ]
    
    try:
        # Set PYTHONPATH environment variable to include musetalk directory
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{MUSETALK_DIR}{os.pathsep}{env.get('PYTHONPATH', '')}"
        
        # Change to the musetalk directory before running the script
        original_dir = os.getcwd()
        os.chdir(MUSETALK_DIR)
        
        try:
            # Create a process that can handle stdin
            process = subprocess.Popen(
                cmd,
                env=env,
                stdin=subprocess.PIPE,
                text=True
            )
            
            # Send 'y' to the process when it asks about recreating the avatar
            process.communicate(input='y\n')
            
            if process.returncode == 0:
                # Get the result video path
                result_path = MUSETALK_DIR / "results/v15/avatars/avator_1/vid_output/audio_0.mp4"
                if result_path.exists():
                    # Read the video file and convert to base64
                    with open(result_path, 'rb') as f:
                        video_bytes = f.read()
                    return base64.b64encode(video_bytes).decode('utf-8')
                else:
                    raise Exception("Could not find the output video file")
            else:
                raise Exception(f"Inference failed with return code: {process.returncode}")
                
        finally:
            # Change back to the original directory
            os.chdir(original_dir)
            
    except subprocess.CalledProcessError as e:
        raise Exception(f"Inference failed: {e}")

@app.websocket("/ws/lipsync")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Receive the message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Validate input
            if "image_base64" not in message or "audio_base64" not in message:
                await websocket.send_json({
                    "error": "Missing required fields: image_base64 and audio_base64"
                })
                continue
            
            try:
                # Send initial processing message
                await websocket.send_json({
                    "status": "processing",
                    "message": "Starting inference..."
                })
                
                # Decode base64 data
                image_bytes = base64.b64decode(message["image_base64"])
                audio_bytes = base64.b64decode(message["audio_base64"])
                
                # Preprocess image
                processed_image_bytes = preprocess_image(image_bytes)
                
                # Create temporary files
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as img_file:
                    img_file.write(processed_image_bytes)
                    image_path = img_file.name
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_file:
                    audio_file.write(audio_bytes)
                    audio_path = audio_file.name
                
                try:
                    # Run inference
                    video_base64 = run_inference(image_path, audio_path)
                    
                    # Send the result
                    await websocket.send_json({
                        "status": "success",
                        "video_base64": video_base64
                    })
                    
                finally:
                    # Clean up temporary files
                    os.unlink(image_path)
                    os.unlink(audio_path)
                    
            except Exception as e:
                await websocket.send_json({
                    "status": "error",
                    "error": str(e)
                })
                
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        try:
            await websocket.send_json({
                "status": "error",
                "error": str(e)
            })
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 