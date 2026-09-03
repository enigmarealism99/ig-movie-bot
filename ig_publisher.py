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


def publish_reel(video_url, caption, max_retries=5, retry_delay=30):
    """
    1. Buat media container (REELS) -- retry beberapa kali kalau IG belum bisa
       akses video_url (jsDelivr CDN kadang butuh waktu beberapa menit buat
       cache file yang baru di-push).
    2. Poll status sampai FINISHED
    3. Publish container -> jadi post live di Instagram
    """
    create_url = f"{GRAPH_BASE}/{IG_USER_ID}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN,
    }

    creation_id = None
    last_error = None
    for attempt in range(max_retries):
        resp = requests.post(create_url, data=payload, timeout=60)
        if resp.status_code == 200:
            creation_id = resp.json()["id"]
            break
        last_error = resp.text
        time.sleep(retry_delay)

    if creation_id is None:
        raise RuntimeError(f"Gagal buat media container setelah {max_retries}x coba: {last_error}")

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
