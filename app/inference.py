import sys
import os

# Add "app/musetalk" to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "musetalk")))

# Add "app/musetalk/musetalk" to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "musetalk", "musetalk")))

import uuid
import torch
import shutil
import cv2
from omegaconf import OmegaConf
from transformers import WhisperModel

# Local imports (update based on corrected structure)
from scripts.realtime_inference import Avatar, fast_check_ffmpeg
from utils.face_parsing import FaceParsing
from utils.utils import load_all_model
from utils.audio_processor import AudioProcessor


# ---------- Config ----------
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
VAE_TYPE = "sd-vae"
UNET_CONFIG = "./models/musetalk/musetalk.json"
UNET_MODEL_PATH = "./models/musetalk/pytorch_model.bin"
WHISPER_DIR = "./models/whisper"
INFERENCE_CONFIG = "./configs/inference/realtime.yaml"
FFMPEG_PATH = "./ffmpeg-master-latest-win64-gpl-shared/bin"
FPS = 25
BATCH_SIZE = 2
VERSION = "v15"

# ---------- Load Models Once ----------
vae, unet, pe = load_all_model(
    unet_model_path=UNET_MODEL_PATH,
    vae_type=VAE_TYPE,
    unet_config=UNET_CONFIG,
    device=DEVICE
)
timesteps = torch.tensor([0], device=DEVICE)
pe = pe.half().to(DEVICE)
vae.vae = vae.vae.half().to(DEVICE)
unet.model = unet.model.half().to(DEVICE)
audio_processor = AudioProcessor(feature_extractor_path=WHISPER_DIR)
weight_dtype = unet.model.dtype
whisper = WhisperModel.from_pretrained(WHISPER_DIR).to(device=DEVICE, dtype=weight_dtype).eval()
whisper.requires_grad_(False)

# ---------- Face Parsing ----------
fp = FaceParsing(left_cheek_width=90, right_cheek_width=90)


def infer_talking_face(image_path: str, audio_path: str, output_path: str) -> str:
    session_id = str(uuid.uuid4())[:8]
    avatar_id = f"session_{session_id}"
    avatar_path = f"./temp/{avatar_id}"

    # Save single frame from input image
    os.makedirs(avatar_path, exist_ok=True)
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Failed to read image from {image_path}")
    cv2.imwrite(os.path.join(avatar_path, "00000000.png"), img)

    # Prepare config for the Avatar object
    mock_config = {
        avatar_id: {
            "preparation": True,
            "video_path": avatar_path,
            "audio_clips": {
                "output": audio_path
            }
        }
    }

    temp_yaml_path = f"./temp/{avatar_id}.yaml"
    OmegaConf.save(config=OmegaConf.create(mock_config), f=temp_yaml_path)

    # Ensure ffmpeg is found
    if not fast_check_ffmpeg():
        os.environ["PATH"] = f"{FFMPEG_PATH};{os.environ['PATH']}"
        if not fast_check_ffmpeg():
            raise RuntimeError("ffmpeg not found in system path")

    # Run inference
    inference_cfg = OmegaConf.load(temp_yaml_path)
    for avatar_id in inference_cfg:
        info = inference_cfg[avatar_id]
        avatar = Avatar(
            avatar_id=avatar_id,
            video_path=info["video_path"],
            bbox_shift=0,
            batch_size=BATCH_SIZE,
            preparation=info["preparation"]
        )
        for audio_num, audio_path in info["audio_clips"].items():
            avatar.inference(audio_path, audio_num, FPS, skip_save_images=False)

    # Move the result video to desired location
    output_video_path = os.path.join(avatar.video_out_path, "output.mp4")
    shutil.move(output_video_path, output_path)
    return output_path
