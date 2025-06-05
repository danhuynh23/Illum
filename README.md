# Real-time Lip-sync WebSocket API

This project provides a real-time lip-syncing WebSocket API using the MuseTalk model. It takes an image of a person and an audio file as input and generates a video of the person speaking with lip movements synchronized to the audio.

## Features

- Real-time WebSocket communication
- Base64-encoded input/output for easy integration
- Docker support for easy deployment
- GPU acceleration support
- Automatic image preprocessing
- Support for multiple languages (Chinese, English, Japanese)
- Real-time inference with 30fps+ on NVIDIA GPUs

## Prerequisites

- Python 3.10 or higher
- CUDA-compatible GPU (recommended)
- Docker (for containerized deployment)
- FFmpeg (required for video processing)

## Installation

### Local Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create and activate a Python virtual environment:
```bash
conda create -n lipsync python==3.10
conda activate lipsync
```

3. Install PyTorch 2.0.1:
```bash
# Option 1: Using pip
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118

# Option 2: Using conda
conda install pytorch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 pytorch-cuda=11.8 -c pytorch -c nvidia
```

4. Install Python dependencies:
```bash
pip install -r requirements.txt
```

5. Install MMLab packages:
```bash
pip install --no-cache-dir -U openmim
mim install mmengine
mim install "mmcv==2.0.1"
mim install "mmdet==3.1.0"
mim install "mmpose==1.1.0"
```

6. Setup FFmpeg:
   - [Download](https://github.com/BtbN/FFmpeg-Builds/releases) the ffmpeg-static package
   - For Windows: Add the `ffmpeg-xxx\bin` directory to your system's PATH
   - For Linux: Set the FFMPEG_PATH environment variable:
     ```bash
     export FFMPEG_PATH=/path/to/ffmpeg
     ```

7. Download required models:
```bash
# Create model directories
mkdir -p app/models/musetalk app/models/whisper app/models/syncnet app/models/dwpose app/models/face-parse-bisent app/models/sd-vae

# Download model weights from:
# - MuseTalk: https://huggingface.co/TMElyralab/MuseTalk/tree/main
# - sd-vae-ft-mse: https://huggingface.co/stabilityai/sd-vae-ft-mse/tree/main
# - whisper: https://huggingface.co/openai/whisper-tiny/tree/main
# - dwpose: https://huggingface.co/yzd-v/DWPose/tree/main
# - syncnet: https://huggingface.co/ByteDance/LatentSync/tree/main
# - face-parse-bisent: https://drive.google.com/file/d/154JgKpzCPW82qINcVieuPH3fZ2e0P812/view?pli=1
# - resnet18: https://download.pytorch.org/models/resnet18-5c106cde.pth
```

### Docker Installation

1. Build the Docker image:
```bash
docker build -t lipsync-api .
```

2. Run the container:
```bash
# For GPU support
docker run --gpus all -p 8000:8000 lipsync-api

# For CPU-only
docker run -p 8000:8000 lipsync-api
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
- Recommended input video frame rate: 25fps
- Real-time inference can achieve 30fps+ on NVIDIA Tesla V100

## Limitations

- Resolution: The face region size is 256 x 256. For higher resolution, consider using super-resolution models like GFPGAN
- Identity preservation: Some facial details (mustache, lip shape, color) may not be perfectly preserved
- Jitter: Some jitter may occur due to single-frame generation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license information here] 