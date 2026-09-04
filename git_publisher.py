"""
git_publisher.py
Upload video hasil generate ke repo GitHub (folder media/), lalu kembalikan URL
publik lewat jsDelivr CDN -- ini yang dipakai sebagai `video_url` buat Instagram
Graph API. Gratis, gak butuh hosting/server tambahan.

Asumsi: Termux sudah punya git terpasang & repo ini sudah di-clone dengan remote
GitHub yang benar (lihat README bagian Termux Setup).
"""

import os
import time
import subprocess
import requests

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

    # Commit dulu SEBELUM pull -- kalau ada sisa file dari run sebelumnya yang
    # belum ke-commit, itu bikin "git pull --rebase" nolak jalan (unstaged
    # changes). Commit semua dulu baru pull, biar urutan aman.
    _run("git add -A")
    _run(f"git commit -m 'Auto: tambah video {filename}' --allow-empty")
    _run("git pull --rebase")
    _run(f"git push origin {GITHUB_BRANCH}")

    jsdelivr_url = (
        f"https://cdn.jsdelivr.net/gh/{GITHUB_USERNAME}/{GITHUB_REPO}"
        f"@{GITHUB_BRANCH}/media/{filename}"
    )

    # jsDelivr butuh waktu buat cache file yang BARU pertama kali -- tunggu
    # sampai beneran bisa diakses (bukan cuma asumsi delay tetap)
    _wait_until_accessible(jsdelivr_url)

    return jsdelivr_url


def _wait_until_accessible(url, max_attempts=15, delay=10):
    """
    Poll URL pakai GET request (bukan HEAD -- jsDelivr kadang cuma warm cache
    dari GET beneran) sampai dapat 200 OK dengan body yang valid, atau
    nyerah setelah max_attempts.
    """
    for attempt in range(max_attempts):
        try:
            resp = requests.get(url, timeout=20, stream=True)
            if resp.status_code == 200:
                # baca sedikit body buat mastiin beneran ke-download, bukan cuma header
                chunk = next(resp.iter_content(chunk_size=1024), None)
                resp.close()
                if chunk:
                    return True
        except requests.RequestException:
            pass
        time.sleep(delay)
    raise RuntimeError(
        f"URL jsDelivr belum bisa diakses setelah {max_attempts * delay} detik: {url}"
    )


def cleanup_old_video(filename):
    """
    Opsional: hapus video lama dari repo setelah berhasil publish, biar repo
    gak numpuk file besar terus-terusan.
    """
    dest_path = os.path.join(REPO_DIR, "media", filename)
    if os.path.exists(dest_path):
        os.remove(dest_path)
    _run("git add -A")
    _run(f"git commit -m 'Auto: hapus video lama {filename}' --allow-empty")
    _run("git pull --rebase")
    _run(f"git push origin {GITHUB_BRANCH}")
