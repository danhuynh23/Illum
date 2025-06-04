import asyncio
import websockets
import json
import base64
import argparse
from pathlib import Path

async def test_lipsync(image_path, audio_path):
    # Read and encode files
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    with open(audio_path, 'rb') as f:
        audio_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # Prepare request
    request = {
        "image_base64": image_base64,
        "audio_base64": audio_base64
    }
    
    # Connect to WebSocket with longer timeout
    uri = "ws://localhost:8000/ws/lipsync"
    async with websockets.connect(uri, ping_interval=30, ping_timeout=120) as websocket:
        print("Connected to WebSocket server")
        
        # Send request
        print("Sending request...")
        await websocket.send(json.dumps(request))
        
        # Wait for response
        print("Waiting for response...")
        while True:
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get("status") == "processing":
                print(f"Status: {response_data.get('message', 'Processing...')}")
                continue
                
            if response_data.get("status") == "error":
                print(f"Error: {response_data.get('error', 'Unknown error')}")
                return
                
            if response_data.get("status") == "success":
                # Save video
                video_base64 = response_data["video_base64"]
                video_bytes = base64.b64decode(video_base64)
                
                output_path = Path("output.mp4")
                with open(output_path, 'wb') as f:
                    f.write(video_bytes)
                
                print(f"Video saved to: {output_path}")
                return

def main():
    parser = argparse.ArgumentParser(description='Test the lip-sync WebSocket API')
    parser.add_argument('--image', type=str, required=True, help='Path to input image file')
    parser.add_argument('--audio', type=str, required=True, help='Path to input audio file')
    
    args = parser.parse_args()
    
    asyncio.run(test_lipsync(args.image, args.audio))

if __name__ == "__main__":
    main() 