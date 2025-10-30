import requests

API_URL = "https://your-lipsync-api.onrender.com/generate/"

video_path = "input_face.mp4"
audio_path = "sample_voice.wav"

files = {
    "video": ("input_face.mp4", open(video_path, "rb"), "video/mp4"),
    "audio": ("sample_voice.wav", open(audio_path, "rb"), "audio/wav"),
}

print("🚀 Sending request to API...")
response = requests.post(API_URL, files=files)

if response.status_code == 200:
    with open("lip_synced_output.mp4", "wb") as f:
        f.write(response.content)
    print("✅ Lip-synced video saved as lip_synced_output.mp4")
else:
    print("❌ Error:", response.status_code)
    print(response.text)
