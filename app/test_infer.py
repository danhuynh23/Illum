from inference import infer_talking_face

if __name__ == "__main__":
    image_path = "./app/inputs/sample.jpg"           # Change to your test image
    audio_path = "./app/inputs/audio.wav"            # Change to your test audio
    output_path = "./app/outputs/final_output.mp4"   # Your desired output path

    try:
        result = infer_talking_face(image_path, audio_path, output_path)
        print("✅ Generated talking video at:", result)
    except Exception as e:
        print("❌ Inference failed:", e)
