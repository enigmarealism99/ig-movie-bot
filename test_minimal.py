"""
test_minimal.py
Diagnostik: bikin video paling simpel yang mungkin (warna solid + audio senyap,
spek paling aman sesuai dokumentasi resmi Reels), lalu coba publish.

Tujuannya: isolasi apakah masalah ada di proses generate video kita (ffmpeg
settings) atau di tempat lain (URL/token/permission/jsDelivr).

Jalankan: python test_minimal.py
"""

import os
import subprocess
import uuid
from dotenv import load_dotenv

load_dotenv()

from git_publisher import publish_video_to_github, cleanup_old_video
from ig_publisher import publish_reel

MEDIA_DIR = os.path.join(os.path.dirname(__file__), "media")
os.makedirs(MEDIA_DIR, exist_ok=True)

filename = f"test_{uuid.uuid4().hex}.mp4"
output_path = os.path.join(MEDIA_DIR, filename)

print("Generate video test paling simpel (5 detik, warna solid + audio senyap)...")
cmd = [
    "ffmpeg", "-y",
    "-f", "lavfi", "-i", "color=c=blue:s=1080x1920:d=5:r=30",
    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
    "-c:v", "libx264", "-profile:v", "baseline", "-pix_fmt", "yuv420p",
    "-g", "60", "-keyint_min", "60", "-sc_threshold", "0",
    "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
    "-shortest",
    "-movflags", "+faststart",
    output_path,
]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print("Gagal generate video test:", result.stderr)
    exit(1)

print(f"Video test selesai: {output_path} ({os.path.getsize(output_path)} bytes)")

print("Push ke GitHub...")
video_url = publish_video_to_github(output_path, filename)
print(f"URL publik: {video_url}")

print("Publish ke Instagram...")
try:
    result = publish_reel(video_url, "Test video sederhana dari bot")
    print("BERHASIL:", result)
except Exception as e:
    print("GAGAL:", e)
finally:
    os.remove(output_path)
    cleanup_old_video(filename)
