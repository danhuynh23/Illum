# Real-Time Lip-Syncing WebSocket API

This project provides a real-time lip-syncing WebSocket API using FastAPI and the Wav2Lip model. It accepts base64-encoded audio and image inputs and returns a base64-encoded video output.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd lip-sync-api
   ```

2. Install dependencies:
   ```bash
   pip install -r app/requirements.txt
   ```

3. Run the API:
   ```bash
   uvicorn app.main:app --reload
   ```

## How It Works

- The API uses FastAPI to provide a WebSocket endpoint at `/ws`.
- It accepts JSON payloads with base64-encoded audio and image data.
- The Wav2Lip model processes the inputs and returns a base64-encoded video.

## Testing with a WebSocket Client

You can test the API using a WebSocket client (e.g., `websocat` or a browser-based client). Example payload:

```json
{
  "audio": "<base64-encoded-audio>",
  "image": "<base64-encoded-image>"
}
```

## Running with Docker

1. Build the Docker image:
   ```bash
   docker build -t lip-sync-api .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 lip-sync-api
   ```

The API will be available at `ws://localhost:8000/ws`. 