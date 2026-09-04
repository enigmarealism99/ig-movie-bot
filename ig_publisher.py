"""ig_publisher.py - FINAL
Publish Reels ke Instagram via Graph API.
Fix: validasi, retry, poll, error detail.
"""

import os, time, requests

IG_USER_ID = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
GRAPH_BASE = "https://graph.facebook.com/v20.0"


def _validate_video(path):
    import subprocess, json
    try:
        cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
               '-show_entries', 'stream=width,height,codec_name,pix_fmt,r_frame_rate',
               '-of', 'json', path]
        info = json.loads(subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout)
        s = info['streams'][0]
        w, h, codec, fps = s['width'], s['height'], s['codec_name'], eval(s['r_frame_rate'])
        issues = []
        if codec != 'h264':
            issues.append(f"codec={codec}")
        if not (0.55 < w/h < 0.57):
            issues.append(f"ratio={w/h:.2f}")
        if fps > 31:
            issues.append(f"fps={fps}")
        return (len(issues) == 0, "; ".join(issues) if issues else "OK")
    except Exception as e:
        return (False, str(e))


def _download_video(url, path, retries=10):
    for i in range(retries):
        try:
            r = requests.get(url, timeout=60, stream=True)
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"   (percobaan download {i+1}/{retries} gagal: {e})")
            if i < retries - 1:
                time.sleep(10)
    return False


def publish_reel(video_url, caption, local_video_path=None, max_retries=3, retry_delay=30):
    temp_path = None
    video_path = local_video_path

    if not video_path or not os.path.exists(video_path):
        temp_path = f"/tmp/ig_video_{os.getpid()}.mp4"
        if not _download_video(video_url, temp_path):
            raise RuntimeError("Gagal download video")
        video_path = temp_path

    valid, msg = _validate_video(video_path)
    if not valid:
        raise RuntimeError(f"Video invalid: {msg}")
    print(f"✅ Video valid: {msg}")

    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN,
    }

    creation_id = None
    for i in range(max_retries):
        r = requests.post(f"{GRAPH_BASE}/{IG_USER_ID}/media", data=payload, timeout=60)
        if r.status_code == 200:
            creation_id = r.json()["id"]
            break
        print(f"⚠️ Attempt {i+1}/{max_retries}: {r.text[:200]}")
        time.sleep(retry_delay)

    if not creation_id:
        raise RuntimeError("Gagal buat media container")

    print(f"✅ Container: {creation_id}")

    for i in range(60):
        r = requests.get(f"{GRAPH_BASE}/{creation_id}",
                        params={"fields": "status_code,status", "access_token": IG_ACCESS_TOKEN},
                        timeout=30)
        r.raise_for_status()
        data = r.json()
        status = data.get("status_code")
        print(f"   [{i+1}/60] {status}")

        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError(f"IG error: {data.get('status', 'Unknown')}")
        time.sleep(10)
    else:
        raise TimeoutError("Timeout 10 menit")

    r = requests.post(f"{GRAPH_BASE}/{IG_USER_ID}/media_publish",
                     data={"creation_id": creation_id, "access_token": IG_ACCESS_TOKEN},
                     timeout=60)
    r.raise_for_status()
    result = r.json()

    if temp_path and os.path.exists(temp_path):
        os.remove(temp_path)

    print(f"✅ Published: {result.get('id')}")
    return result


def post_comment(media_id, text):
    """Post komentar ke media tertentu."""
    url = f"{GRAPH_BASE}/{media_id}/comments"
    payload = {
        "message": text,
        "access_token": IG_ACCESS_TOKEN,
    }
    r = requests.post(url, data=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def reply_to_comment(comment_id, text):
    """Reply ke komentar user."""
    url = f"{GRAPH_BASE}/{comment_id}/replies"
    payload = {
        "message": text,
        "access_token": IG_ACCESS_TOKEN,
    }
    r = requests.post(url, data=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def get_recent_comments(media_id, limit=10):
    """Ambil komentar terbaru dari post."""
    url = f"{GRAPH_BASE}/{media_id}/comments"
    params = {
        "fields": "id,text,username,timestamp",
        "limit": limit,
        "access_token": IG_ACCESS_TOKEN,
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("data", [])
