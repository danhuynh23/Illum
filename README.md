# MuseTalk WebSocket API

A real-time lip-syncing WebSocket API that uses the MuseTalk model to animate a speaking person from audio and image input.

## Features

- Real-time WebSocket communication
- Base64-encoded input/output for audio and video
- Docker support with CUDA
- FastAPI backend

## Prerequisites

- NVIDIA GPU with CUDA support
- Docker and nvidia-docker installed
- Git

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. Build the Docker image:
   ```bash
   docker build -t musetalk-api .
   ```

## Running the API

1. Start the Docker container:
   ```bash
   docker run --gpus all -p 8000:8000 musetalk-api
   ```

The API will be available at `ws://localhost:8000/ws/lipsync`

## Testing with WebSocket Client

Here's a simple Python script to test the API:

```python
import asyncio
import websockets
import json
import base64

async def test_lipsync():
    uri = "ws://localhost:8000/ws/lipsync"
    async with websockets.connect(uri) as websocket:
        # Read your image and audio files
        with open("path/to/image.jpg", "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode()
        with open("path/to/audio.wav", "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode()
        
        # Send request
        await websocket.send(json.dumps({
            "image_base64": image_base64,
            "audio_base64": audio_base64
        }))
        
        # Receive response
        response = await websocket.recv()
        result = json.loads(response)
        
        if result["status"] == "success":
            # Save the video
            video_data = base64.b64decode(result["video_base64"])
            with open("output.mp4", "wb") as f:
                f.write(video_data)
            print("Video saved as output.mp4")
        else:
            print("Error:", result["message"])

asyncio.run(test_lipsync())
```

## API Specification

### WebSocket Endpoint: `/ws/lipsync`

#### Input Format
```json
{
    "image_base64": "base64-encoded-image-string",
    "audio_base64": "base64-encoded-audio-string"
}
```

#### Output Format
```json
{
    "status": "success|error",
    "video_base64": "base64-encoded-video-string" // if status is success
    "message": "error-message" // if status is error
}
```

## Notes

- The input image should contain a single person's face
- Supported audio format: WAV
- The API uses temporary storage for processing
- GPU memory requirements: minimum 8GB recommended

## License

[Your License] 