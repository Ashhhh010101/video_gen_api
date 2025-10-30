from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
import os
import uuid
import shutil
import subprocess
import requests

app = FastAPI(title="Lip Sync Video Generator (Wav2Lip)", version="1.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
MODEL_PATH = os.path.join(BASE_DIR, "wav2lip_gan.pth")
WAV2LIP_DIR = os.path.join(BASE_DIR, "wav2lip")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Hugging Face Wav2Lip model weights
MODEL_URL = "https://huggingface.co/spaces/aarushsu/wav2lip/resolve/main/wav2lip_gan.pth"


def download_file(url, dest_path):
    """Download file from URL."""
    print(f"📥 Downloading {url} -> {dest_path}")
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(dest_path, "wb") as f:
            shutil.copyfileobj(r.raw, f)
        print("✅ Download complete.")
        return True
    print(f"❌ Failed to download from {url}")
    return False


def setup_environment():
    """Clone Wav2Lip repo and download model if missing."""
    # Clone Wav2Lip
    if not os.path.exists(WAV2LIP_DIR):
        print("📦 Cloning Wav2Lip repository...")
        subprocess.run(["git", "clone", "https://github.com/Rudrabha/Wav2Lip.git", WAV2LIP_DIR], check=True)
        print("✅ Wav2Lip cloned successfully!")

    # Download pretrained model
    if not os.path.exists(MODEL_PATH):
        print("📥 Downloading pretrained model weights...")
        if not download_file(MODEL_URL, MODEL_PATH):
            raise Exception("Failed to download Wav2Lip model weights!")


# Run setup once at startup
setup_environment()


@app.get("/")
def root():
    return {"message": "Lip Sync Generator API is running 🚀"}


@app.post("/generate/")
async def generate_lip_sync(
    audio: UploadFile = File(None),
    video: UploadFile = File(None),
    audio_url: str = Form(None),
    video_url: str = Form(None),
):
    """
    Generate lip-synced video using Wav2Lip.
    Supports both file upload and URL inputs.
    """
    audio_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_audio.wav")
    video_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_video.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"output_{uuid.uuid4()}.mp4")

    # Handle audio
    if audio:
        with open(audio_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)
    elif audio_url:
        if not download_file(audio_url, audio_path):
            return JSONResponse({"error": "Failed to download audio"}, status_code=400)
    else:
        return JSONResponse({"error": "Audio missing"}, status_code=400)

    # Handle video
    if video:
        with open(video_path, "wb") as f:
            shutil.copyfileobj(video.file, f)
    elif video_url:
        if not download_file(video_url, video_path):
            return JSONResponse({"error": "Failed to download video"}, status_code=400)
    else:
        return JSONResponse({"error": "Video missing"}, status_code=400)

    # Run Wav2Lip inference
    command = [
        "python", os.path.join(WAV2LIP_DIR, "inference.py"),
        "--checkpoint_path", MODEL_PATH,
        "--face", video_path,
        "--audio", audio_path,
        "--outfile", output_path
    ]

    try:
        print("🚀 Running Wav2Lip inference...")
        subprocess.run(command, check=True)
        print("✅ Lip-sync video generated!")
    except subprocess.CalledProcessError as e:
        return JSONResponse({"error": f"Wav2Lip failed: {e}"}, status_code=500)

    return FileResponse(output_path, media_type="video/mp4", filename="lip_synced_output.mp4")
