import asyncio
import websockets
import json
import base64
import argparse
from pathlib import Path
import time

# Get the absolute path to the client directory
CLIENT_DIR = Path(__file__).parent.absolute()
INPUT_DIR = CLIENT_DIR / "inputs"
OUTPUT_DIR = CLIENT_DIR / "outputs"

async def heartbeat(websocket):
    """Send periodic heartbeat to keep connection alive"""
    while True:
        try:
            await websocket.ping()
            await asyncio.sleep(10)  # Send ping every 10 seconds
        except Exception as e:
            print(f"Heartbeat error: {e}")
            break

async def test_lipsync(image_path, audio_path):
    # Read and encode files
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    with open(audio_path, 'rb') as f:
        audio_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # Connect to WebSocket with much longer timeout
    uri = "ws://localhost:8000/ws/lipsync"
    async with websockets.connect(
        uri,
        ping_interval=None,  # Disable automatic pings
        ping_timeout=None,   # Disable ping timeout
        close_timeout=None,  # Disable close timeout
        max_size=None        # Disable message size limit
    ) as websocket:
        print("Connected to WebSocket server")
        
        # Start heartbeat in background
        heartbeat_task = asyncio.create_task(heartbeat(websocket))
        
        try:
            # Send request
            request = {
                "image_base64": image_base64,
                "audio_base64": audio_base64
            }
            print("Sending request...")
            await websocket.send(json.dumps(request))
            
            print("Waiting for response...")
            start_time = time.time()
            while True:
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    if "status" in data:
                        if "message" in data:
                            print(f"Status: {data['message']}")
                        if data["status"] == "success":
                            if "video_base64" in data:
                                # Save the video to client's output directory with timestamp
                                video_bytes = base64.b64decode(data["video_base64"])
                                timestamp = int(time.time())
                                output_path = OUTPUT_DIR / "videos" / f"output_{timestamp}.mp4"
                                with open(output_path, "wb") as f:
                                    f.write(video_bytes)
                                print(f"Video saved to {output_path}")
                                break
                            else:
                                print("Error: No video data in response")
                                break
                        elif data["status"] == "error":
                            print(f"Error: {data.get('error', 'Unknown error')}")
                            break
                        else:
                            print(f"Unknown status: {data['status']}")
                            continue
                    else:
                        print(f"Unexpected response format: {data}")
                        break
                except websockets.exceptions.ConnectionClosed as e:
                    print(f"Connection closed: {e}")
                    print(f"Time elapsed: {time.time() - start_time:.2f} seconds")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    print(f"Time elapsed: {time.time() - start_time:.2f} seconds")
                    break
        finally:
            # Cancel heartbeat task
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

def main():
    parser = argparse.ArgumentParser(description='Test the lip-sync WebSocket API')
    parser.add_argument('--image', type=str, required=True, help='Path to input image file')
    parser.add_argument('--audio', type=str, required=True, help='Path to input audio file')
    
    args = parser.parse_args()
    
    # Convert relative paths to absolute paths if they're relative to client/inputs
    image_path = Path(args.image)
    audio_path = Path(args.audio)
    
    if not image_path.is_absolute():
        # If path doesn't start with images/ or audio/, add the appropriate prefix
        if not str(image_path).startswith(('images/', 'images\\')):
            image_path = INPUT_DIR / "images" / image_path.name
        else:
            image_path = INPUT_DIR / image_path
            
        if not str(audio_path).startswith(('audio/', 'audio\\')):
            audio_path = INPUT_DIR / "audio" / audio_path.name
        else:
            audio_path = INPUT_DIR / audio_path
    
    print(f"Using image path: {image_path}")
    print(f"Using audio path: {audio_path}")
    
    asyncio.run(test_lipsync(image_path, audio_path))

if __name__ == "__main__":
    main() 