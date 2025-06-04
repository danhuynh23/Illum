import base64
import io
import tempfile
from pathlib import Path
from typing import Optional
import cv2
import numpy as np
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from pydantic import BaseModel

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

@app.websocket("/ws/lipsync")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Receive and parse input
            data = await websocket.receive_text()
            input_data = json.loads(data)
            
            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Save input files
                image_path = temp_path / "input.jpg"
                audio_path = temp_path / "input.wav"
                save_base64_to_file(input_data["image_base64"], image_path)
                save_base64_to_file(input_data["audio_base64"], audio_path)
                
                # Process with MuseTalk
                from test_infer import run_inference
                result_path = run_inference(
                    image_path=str(image_path),
                    audio_path=str(audio_path),
                    output_dir=str(temp_path)
                )
                
                # Read and send result
                if result_path.exists():
                    video_base64 = get_base64_from_file(result_path)
                    await websocket.send_json({
                        "status": "success",
                        "video_base64": video_base64
                    })
                else:
                    await websocket.send_json({
                        "status": "error",
                        "message": "Failed to generate video"
                    })
                    
    except Exception as e:
        await websocket.send_json({
            "status": "error",
            "message": str(e)
        })
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 