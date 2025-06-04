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
from queue import Queue, Empty
import threading
import yaml
import shutil

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

# Global message queue for communication between sync and async code
message_queue = Queue()

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

async def run_inference(image_path, audio_path, websocket):
    # Ensure output directory exists
    output_dir = APP_DIR / "outputs"
    print(f"Output directory: {output_dir}")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "tmp").mkdir(exist_ok=True)
    (output_dir / "vid_output").mkdir(exist_ok=True)
    
    # Update the config file with the new image and audio paths
    config_path = APP_DIR / "configs/inference/test.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Get relative paths from MUSETALK_DIR
    relative_image_path = os.path.relpath(image_path, MUSETALK_DIR)
    relative_audio_path = os.path.relpath(audio_path, MUSETALK_DIR)
    
    config["avator_1"]["video_path"] = relative_image_path
    config["avator_1"]["audio_clips"]["audio_0"] = relative_audio_path
    config["avator_1"]["output_dir"] = "results/v15/avatars/avator_1"
    config["avator_1"]["tmp_dir"] = "results/v15/avatars/avator_1/tmp"
    config["avator_1"]["vid_output_dir"] = "results/v15/avatars/avator_1/vid_output"
    
    with open(config_path, "w") as f:
        yaml.safe_dump(config, f)
    
    print(f"[Debug] Updated config with image path: {relative_image_path}")
    print(f"[Debug] Updated config with audio path: {relative_audio_path}")
    
    # Send initial message
    await websocket.send_json({
        "status": "processing",
        "message": "Starting inference process..."
    })
    
    # Run the realtime inference script
    cmd = [
        sys.executable,  # Use the current Python interpreter
        str(MUSETALK_DIR / "scripts/realtime_inference.py"),
        "--version", "v15",
        "--inference_config", str(APP_DIR / "configs/inference/test.yaml"),
        "--fps", "20",
        "--batch_size", "3"
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
            
            # Send progress messages at key points
            await websocket.send_json({
                "status": "processing",
                "message": "Loading models and preparing data..."
            })
            
            if process.returncode == 0:
                # Get the result video path from the script's output
                script_output = MUSETALK_DIR / "results/v15/avatars/avator_1/vid_output/audio_0.mp4"
                if script_output.exists():
                    await websocket.send_json({
                        "status": "processing",
                        "message": "Processing complete, preparing final video..."
                    })
                    
                    # Copy the file to our output directory
                    our_output = output_dir / "result.mp4"
                    shutil.copy2(script_output, our_output)
                    
                    # Read the video file and convert to base64
                    with open(our_output, 'rb') as f:
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

async def send_messages(websocket):
    """Async function to send messages from queue to WebSocket"""
    while True:
        try:
            # Get message from queue with timeout
            message = message_queue.get(timeout=0.1)
            await websocket.send_json({
                "status": "processing",
                "message": message
            })
        except Empty:
            # No messages in queue, continue
            continue
        except Exception as e:
            print(f"Error sending message: {e}")
            break

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
                
                # Decode and preprocess the image
                image_bytes = base64.b64decode(message["image_base64"])
                processed_image_bytes = preprocess_image(image_bytes)
                
                # Save the processed image
                image_path = APP_DIR / "inputs" / "current_image.jpg"
                with open(image_path, 'wb') as f:
                    f.write(processed_image_bytes)
                
                # Save the audio
                audio_bytes = base64.b64decode(message["audio_base64"])
                audio_path = APP_DIR / "inputs" / "current_audio.wav"
                with open(audio_path, 'wb') as f:
                    f.write(audio_bytes)
                
                print(f"[Debug] Saved processed image to: {image_path}")
                print(f"[Debug] Saved audio to: {audio_path}")
                
                # Start message sender in background
                message_sender = asyncio.create_task(send_messages(websocket))
                
                # Run inference
                video_base64 = await run_inference(image_path, audio_path, websocket)
                
                # Cancel message sender
                message_sender.cancel()
                
                # Send the result
                await websocket.send_json({
                    "status": "success",
                    "video_base64": video_base64
                })
                
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