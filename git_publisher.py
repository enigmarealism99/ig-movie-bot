"""git_publisher.py
Push video ke GitHub, return URL jsDelivr.
"""

import os, subprocess

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
REPO_DIR = os.path.dirname(os.path.abspath(__file__))


def _run(cmd):
    r = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True, shell=True)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd}\n{r.stderr}")
    return r.stdout


def publish_video_to_github(local_path, filename):
    if not GITHUB_USERNAME or not GITHUB_REPO:
        raise RuntimeError("GITHUB_USERNAME/REPO belum diset di .env")

    dest = os.path.join(REPO_DIR, "media", filename)
    if os.path.abspath(local_path) != os.path.abspath(dest):
        _run(f"cp '{local_path}' '{dest}'")

    _run("git pull --rebase")
    _run(f"git add media/{filename}")
    _run(f"git commit -m 'Auto: tambah video {filename}'")
    _run(f"git push origin {GITHUB_BRANCH}")

    return f"https://cdn.jsdelivr.net/gh/{GITHUB_USERNAME}/{GITHUB_REPO}@{GITHUB_BRANCH}/media/{filename}"


def cleanup_old_video(filename):
    dest = os.path.join(REPO_DIR, "media", filename)
    if os.path.exists(dest):
        os.remove(dest)
        _run(f"git add media/{filename}")
        _run(f"git commit -m 'Auto: hapus video {filename}'")
        _run(f"git push origin {GITHUB_BRANCH}")
