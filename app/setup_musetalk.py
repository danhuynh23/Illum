import os
import subprocess
import shutil
from pathlib import Path

def setup_musetalk():
    # Create necessary directories
    os.makedirs("app/musetalk/utils/dwpose", exist_ok=True)
    
    # Clone MuseTalk repository if not exists
    if not os.path.exists("app/musetalk/utils/dwpose/rtmpose-l_8xb32-270e_coco-ubody-wholebody-384x288.py"):
        print("Downloading MuseTalk configuration files...")
        subprocess.run([
            "git", "clone", "https://github.com/TMElyralab/MuseTalk.git", "temp_musetalk"
        ], check=True)
        
        # Copy required files
        shutil.copytree(
            "temp_musetalk/musetalk/utils/dwpose",
            "app/musetalk/utils/dwpose",
            dirs_exist_ok=True
        )
        
        # Clean up
        shutil.rmtree("temp_musetalk")
        
        print("✅ MuseTalk setup completed successfully!")
    else:
        print("✅ MuseTalk is already set up!")

if __name__ == "__main__":
    setup_musetalk() 