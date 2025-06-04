# Real-time Lip-sync WebSocket API

This project provides a real-time lip-syncing WebSocket API using the MuseTalk model. It takes an image of a person and an audio file as input and generates a video of the person speaking with lip movements synchronized to the audio.

## Features

- Real-time WebSocket communication
- Base64-encoded input/output for easy integration
- Docker support for easy deployment
- GPU acceleration support
- Automatic image preprocessing

## Prerequisites

- Python 3.10 or higher
- CUDA-compatible GPU (recommended)
- Docker (for containerized deployment)

## Installation

### Local Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Download the required models:
```bash
# Create model directories
mkdir -p app/models/musetalk app/models/whisper

# Download MuseTalk model files
# (Add instructions for downloading model files)
```

### Docker Installation

1. Build the Docker image:
```bash
docker build -t lipsync-api .
```

2. Run the container:
```bash
docker run --gpus all -p 8000:8000 lipsync-api
```

## Usage

### Starting the API Server

#### Local
```bash
cd app
python api.py
```

#### Docker
```bash
docker run --gpus all -p 8000:8000 lipsync-api
```

### Testing with the Test Client

The repository includes a test client that can be used to verify the API functionality:

```bash
cd app
python test_client.py --image path/to/image.jpg --audio path/to/audio.wav
```

### WebSocket API

Connect to the WebSocket endpoint at `ws://localhost:8000/ws/lipsync`

#### Request Format
```json
{
    "image_base64": "<base64-encoded-image>",
    "audio_base64": "<base64-encoded-audio>"
}
```

#### Response Format
```json
{
    "video_base64": "<base64-encoded-video>"
}
```

Or in case of an error:
```json
{
    "error": "<error-message>"
}
```

## System Architecture

1. **WebSocket Server**: Handles real-time communication with clients
2. **Image Preprocessing**: Resizes and normalizes input images
3. **MuseTalk Model**: Generates lip-synced video from image and audio
4. **Video Processing**: Converts the output to base64 format

## Error Handling

The API includes comprehensive error handling for:
- Invalid input formats
- Missing required fields
- Model inference errors
- File system errors

## Performance Considerations

- The API uses GPU acceleration when available
- Images are automatically resized to optimize processing
- Temporary files are cleaned up after processing
- WebSocket connection is maintained for real-time communication

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license information here] 