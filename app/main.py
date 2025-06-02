from fastapi import FastAPI, WebSocket
import base64
import json
from model import load_model, run_inference

app = FastAPI()
model = load_model()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            audio_b64 = payload.get("audio")
            image_b64 = payload.get("image")
            if not audio_b64 or not image_b64:
                await websocket.send_text(json.dumps({"error": "Missing audio or image data"}))
                continue
            audio_bytes = base64.b64decode(audio_b64)
            image_bytes = base64.b64decode(image_b64)
            output_video = run_inference(model, image_bytes, audio_bytes)
            output_b64 = base64.b64encode(output_video).decode("utf-8")
            await websocket.send_text(json.dumps({"video": output_b64}))
    except Exception as e:
        await websocket.send_text(json.dumps({"error": str(e)})) 