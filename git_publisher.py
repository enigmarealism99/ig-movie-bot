"""
git_publisher.py
Upload video hasil generate ke repo GitHub (folder media/), lalu kembalikan URL
publik lewat jsDelivr CDN -- ini yang dipakai sebagai `video_url` buat Instagram
Graph API. Gratis, gak butuh hosting/server tambahan.

Asumsi: Termux sudah punya git terpasang & repo ini sudah di-clone dengan remote
GitHub yang benar (lihat README bagian Termux Setup).
"""

import os
import subprocess

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
REPO_DIR = os.path.dirname(os.path.abspath(__file__))


def _run(cmd):
    result = subprocess.run(
        cmd, cwd=REPO_DIR, capture_output=True, text=True, shell=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command gagal: {cmd}\n{result.stderr}")
    return result.stdout


def publish_video_to_github(local_video_path, filename):
    """
    Copy video ke folder media/, commit, push ke GitHub.
    Return URL publik jsDelivr yang siap dipakai Instagram Graph API.
    """
    if not GITHUB_USERNAME or not GITHUB_REPO:
        raise RuntimeError("GITHUB_USERNAME / GITHUB_REPO belum diset di .env")

    dest_path = os.path.join(REPO_DIR, "media", filename)
    if os.path.abspath(local_video_path) != os.path.abspath(dest_path):
        _run(f"cp '{local_video_path}' '{dest_path}'")

    # Tarik perubahan terbaru dulu biar gak konflik, lalu commit & push
    _run("git pull --rebase")
    _run(f"git add media/{filename}")
    _run(f"git commit -m 'Auto: tambah video {filename}'")
    _run(f"git push origin {GITHUB_BRANCH}")

    jsdelivr_url = (
        f"https://cdn.jsdelivr.net/gh/{GITHUB_USERNAME}/{GITHUB_REPO}"
        f"@{GITHUB_BRANCH}/media/{filename}"
    )

    # jsDelivr biasanya butuh beberapa menit untuk cache CDN pertama kali
    # ambil file baru -- ini ditangani dengan retry ringan di ig_publisher.py
    return jsdelivr_url


def cleanup_old_video(filename):
    """
    Opsional: hapus video lama dari repo setelah berhasil publish, biar repo
    gak numpuk file besar terus-terusan.
    """
    dest_path = os.path.join(REPO_DIR, "media", filename)
    if os.path.exists(dest_path):
        os.remove(dest_path)
        _run(f"git add media/{filename}")
        _run(f"git commit -m 'Auto: hapus video lama {filename}'")
        _run(f"git push origin {GITHUB_BRANCH}")
