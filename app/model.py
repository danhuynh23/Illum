import torch
import base64
import tempfile
import os
import subprocess

from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM
from diffusers import StableDiffusionPipeline

# Setup MuseTalk model from HF
def load_model():
    model = AutoModelForCausalLM.from_pretrained("TMElyralab/MuseTalk")
    processor = AutoProcessor.from_pretrained("TMElyralab/MuseTalk")
    return model, processor

# Save binary to file
def save_temp_file(suffix, data):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(data)
    tmp.close()
    return tmp.name

# Run inference with MuseTalk
def run_inference(model_tuple, image_bytes, audio_bytes):
    model, processor = model_tuple
    image_path = save_temp_file(".jpg", image_bytes)
    audio_path = save_temp_file(".wav", audio_bytes)
    output_path = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name

    # Call MuseTalk CLI or module (MuseTalk uses CLI in their repo)
    cmd = [
        "python3", "inference.py",
        "--driven_audio", audio_path,
        "--source_image", image_path,
        "--output_path", output_path,
        "--pretrained_model_path", "Ali-vilab/MuseTalk"
    ]
    subprocess.run(cmd, check=True)

    with open(output_path, "rb") as f:
        video_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Clean up
    os.unlink(image_path)
    os.unlink(audio_path)
    os.unlink(output_path)

    return video_b64
