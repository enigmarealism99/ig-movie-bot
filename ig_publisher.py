"""
ig_publisher.py
Publish video sebagai Reels ke Instagram lewat Instagram Graph API.
Video harus sudah bisa diakses lewat URL publik (di-hosting oleh app ini sendiri,
lihat main.py route /media/<filename>).
"""

import os
import time
import requests

IG_USER_ID = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
GRAPH_BASE = "https://graph.facebook.com/v20.0"


def publish_reel(video_url, caption):
    """
    1. Buat media container (REELS)
    2. Poll status sampai FINISHED
    3. Publish container -> jadi post live di Instagram
    """
    # Step 1: create container
    create_url = f"{GRAPH_BASE}/{IG_USER_ID}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN,
    }
    resp = requests.post(create_url, data=payload, timeout=60)
    resp.raise_for_status()
    creation_id = resp.json()["id"]

    # Step 2: poll status_code sampai FINISHED (video sedang diproses server IG)
    status_url = f"{GRAPH_BASE}/{creation_id}"
    for _ in range(30):  # max ~5 menit nunggu (30 x 10 detik)
        status_resp = requests.get(
            status_url,
            params={"fields": "status_code", "access_token": IG_ACCESS_TOKEN},
            timeout=30,
        )
        status_resp.raise_for_status()
        status = status_resp.json().get("status_code")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError(f"IG gagal proses video: {status_resp.json()}")
        time.sleep(10)
    else:
        raise TimeoutError("Timeout nunggu IG selesai proses video")

    # Step 3: publish
    publish_url = f"{GRAPH_BASE}/{IG_USER_ID}/media_publish"
    publish_resp = requests.post(
        publish_url,
        data={"creation_id": creation_id, "access_token": IG_ACCESS_TOKEN},
        timeout=60,
    )
    publish_resp.raise_for_status()
    return publish_resp.json()
