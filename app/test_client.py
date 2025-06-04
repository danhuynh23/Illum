import asyncio
import websockets
import json
import base64
from pathlib import Path

async def test_lipsync():
    uri = "ws://localhost:8000/ws/lipsync"
    
    # Get the absolute paths to our test files
    current_dir = Path(__file__).parent
    image_path = current_dir / "inputs" / "TrumpPortrait.jpg"
    audio_path = current_dir / "inputs" / "harvard_input.wav"
    
    print(f"Testing with image: {image_path}")
    print(f"Testing with audio: {audio_path}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Read and encode the files
            print("Reading input files...")
            with open(image_path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode()
            with open(audio_path, "rb") as f:
                audio_base64 = base64.b64encode(f.read()).decode()
            
            # Prepare the request
            request = {
                "image_base64": image_base64,
                "audio_base64": audio_base64
            }
            
            print("Sending request to server...")
            await websocket.send(json.dumps(request))
            
            print("Waiting for response...")
            response = await websocket.recv()
            result = json.loads(response)
            
            if result["status"] == "success":
                # Save the video
                output_path = current_dir / "outputs" / "test_output.mp4"
                video_data = base64.b64decode(result["video_base64"])
                with open(output_path, "wb") as f:
                    f.write(video_data)
                print(f"Success! Video saved to: {output_path}")
            else:
                print("Error:", result["message"])
                
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    print("Starting WebSocket test client...")
    asyncio.run(test_lipsync()) 