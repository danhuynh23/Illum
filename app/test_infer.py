import os
import sys
from pathlib import Path
import subprocess
import cv2
import shutil

# Get the absolute path to the app directory
APP_DIR = Path(__file__).parent.absolute()
MUSETALK_DIR = APP_DIR / "musetalk"

# Add both app and musetalk directories to Python path
sys.path.extend([str(APP_DIR), str(MUSETALK_DIR)])

def preprocess_image():
    # Read the original image
    input_path = APP_DIR / "inputs/TrumpPortrait.jpg"
    img = cv2.imread(str(input_path))
    
    # Calculate new dimensions (maintain aspect ratio and ensure even dimensions)
    max_dimension = 1024
    height, width = img.shape[:2]
    if height > width:
        new_height = max_dimension
        new_width = int(width * (max_dimension / height))
    else:
        new_width = max_dimension
        new_height = int(height * (max_dimension / width))
    
    # Ensure dimensions are even
    new_width = new_width - (new_width % 2)
    new_height = new_height - (new_height % 2)
    
    # Resize image
    resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
    
    # Save resized image
    output_path = APP_DIR / "inputs/TrumpPortrait_resized.jpg"
    cv2.imwrite(str(output_path), resized)
    
    # Update config to use resized image
    config_path = APP_DIR / "configs/inference/test.yaml"
    with open(config_path, 'r') as f:
        config_content = f.read()
    
    config_content = config_content.replace(
        "TrumpPortrait.jpg",
        "TrumpPortrait_resized.jpg"
    )
    
    with open(config_path, 'w') as f:
        f.write(config_content)

def run_inference():
    # Preprocess the input image
    preprocess_image()
    
    # Ensure input directories exist
    input_dir = APP_DIR / "inputs"
    input_dir.mkdir(exist_ok=True)
    
    # Ensure output directory exists
    output_dir = APP_DIR / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    # Run the realtime inference script
    cmd = [
        sys.executable,  # Use the current Python interpreter
        str(MUSETALK_DIR / "scripts/realtime_inference.py"),
        "--version", "v15",
        "--inference_config", str(APP_DIR / "configs/inference/test.yaml"),
        "--result_dir", str(output_dir),
        "--fps", "25",
        "--batch_size", "2"
    ]
    
    try:
        # Set PYTHONPATH environment variable to include musetalk directory
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{MUSETALK_DIR}{os.pathsep}{env.get('PYTHONPATH', '')}"
        
        # Change to the musetalk directory before running the script
        original_dir = os.getcwd()
        os.chdir(MUSETALK_DIR)
        
        try:
            # Create a process that can handle stdin
            process = subprocess.Popen(
                cmd,
                env=env,
                stdin=subprocess.PIPE,
                text=True
            )
            
            # Send 'y' to the process when it asks about recreating the avatar
            process.communicate(input='y\n')
            
            if process.returncode == 0:
                print("✅ Inference completed successfully!")
                
                # Copy the result to the desired location
                result_path = MUSETALK_DIR / "results/v15/avatars/avator_1/vid_output/audio_0.mp4"
                if result_path.exists():
                    target_path = output_dir / "result.mp4"
                    shutil.copy2(result_path, target_path)
                    print(f"✅ Result saved to: {target_path}")
                else:
                    print("❌ Could not find the output video file")
                    sys.exit(1)
            else:
                print("❌ Inference failed with return code:", process.returncode)
                sys.exit(1)
                
        finally:
            # Change back to the original directory
            os.chdir(original_dir)
            
    except subprocess.CalledProcessError as e:
        print("❌ Inference failed:", e)
        sys.exit(1)

if __name__ == "__main__":
    run_inference()
