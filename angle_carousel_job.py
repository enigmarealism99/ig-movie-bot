"""
angle_carousel_job.py
"Movie Content Factory" - carousel 1 film dibedah dari berbagai sudut cerita
(Mystery Hook, Hidden Meaning, Character Deep Dive, dst).

BEDA dari carousel_job.py: isi teksnya BUKAN digenerate otomatis dari TMDB,
karena butuh pemahaman jalan cerita film (interpretasi, bukan data mentah).
Alurnya:
  1. Claude bantu tulis draft 7 sudut buat 1 film (di chat).
  2. Kamu simpan draft itu sebagai 1 file .json di content_queue/ready/
     (isi & format lihat ANGLE_TEMPLATE di bawah), edit manual kalau perlu.
  3. Script ini ambil file PALING LAMA di content_queue/ready/, publish ke
     IG, lalu pindahin filenya ke content_queue/published/ (arsip).

Jalankan manual:   python angle_carousel_job.py
Jalankan terjadwal: python angle_carousel_job.py --scheduled
                    (otomatis publish tiap Jumat/Sabtu/Minggu jam 20:00 WIB,
                     ambil 1 file dari queue - kalau queue kosong, dilewati
                     dan dicatat di log biar kamu tau harus nyiapin draft baru)
"""

import os
import sys
import json
import time
import glob
import argparse
import logging
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

from carousel_builder import build_angle_carousel
from git_publisher import publish_images_to_github, cleanup_files
from ig_publisher import publish_carousel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("angle-carousel-job")

BASE_DIR = os.path.dirname(__file__)
MEDIA_DIR = os.path.join(BASE_DIR, "media")
QUEUE_READY_DIR = os.path.join(BASE_DIR, "content_queue", "ready")
QUEUE_PUBLISHED_DIR = os.path.join(BASE_DIR, "content_queue", "published")
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(QUEUE_READY_DIR, exist_ok=True)
os.makedirs(QUEUE_PUBLISHED_DIR, exist_ok=True)

# Contoh format file draft (.json) yang ditaruh di content_queue/ready/
ANGLE_TEMPLATE = {
    "movie_title": "Judul Film",
    "poster_url": "https://image.tmdb.org/t/p/original/xxxx.jpg",
    "angle_key": "mystery",  # salah satu: mystery, hidden_meaning, hidden_detail,
                              # what_would_you_do, character, ending_theory, cultural_remix
    "angle_label": "Mystery Hook",
    "hook": "Kenapa dia ninggalin rumah tanpa bilang siapa-siapa?",
    "slides": [
        "Slide 2: isi teks...",
        "Slide 3: isi teks...",
        "Slide 4: isi teks...",
    ],
    "caption": "Caption lengkap buat postingan ini...",
}


def _next_ready_file():
    files = sorted(glob.glob(os.path.join(QUEUE_READY_DIR, "*.json")), key=os.path.getmtime)
    return files[0] if files else None


def run_angle_job():
    path = _next_ready_file()
    if not path:
        logger.warning(
            "Queue content_queue/ready/ kosong - gak ada yang di-publish. "
            "Siapin draft baru (.json) dulu sebelum jadwal berikutnya."
        )
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"Publish angle carousel: {data['movie_title']} - {data['angle_label']} (dari {os.path.basename(path)})")

    slide_dir = os.path.join(MEDIA_DIR, f"angle_{os.path.splitext(os.path.basename(path))[0]}")
    slide_paths = build_angle_carousel(
        movie_title=data["movie_title"],
        poster_url=data["poster_url"],
        angle_label=data["angle_label"],
        hook=data["hook"],
        slides=data["slides"],
        output_dir=slide_dir,
        accent_key=data.get("angle_key", "default"),
    )

    filenames = [f"{os.path.basename(slide_dir)}_{os.path.basename(p)}" for p in slide_paths]
    pairs = list(zip(slide_paths, filenames))
    urls = publish_images_to_github(pairs)

    result = publish_carousel(urls, data["caption"])
    logger.info(f"Berhasil publish angle carousel: {result.get('id')}")

    # Cleanup file gambar sementara
    cleanup_files(filenames)
    for p in slide_paths:
        os.remove(p)
    os.rmdir(slide_dir)

    # Arsipkan draft yang sudah dipublish (bukan dihapus, biar ada riwayat)
    archived_path = os.path.join(QUEUE_PUBLISHED_DIR, os.path.basename(path))
    os.rename(path, archived_path)
    logger.info(f"Draft diarsip ke: {archived_path}")

    return result


def next_friday_saturday_sunday_8pm():
    """Cari waktu berikutnya yang jatuh di Jumat/Sabtu/Minggu jam 20:00 WIB."""
    now = datetime.now()
    for offset in range(0, 8):
        candidate_date = now + timedelta(days=offset)
        if candidate_date.weekday() in (4, 5, 6):  # 4=Jumat, 5=Sabtu, 6=Minggu
            candidate = candidate_date.replace(hour=20, minute=0, second=0, microsecond=0)
            if candidate > now:
                return candidate
    raise RuntimeError("Gak ketemu slot Jumat/Sabtu/Minggu berikutnya (harusnya gak mungkin)")


def scheduled_loop():
    logger.info("Angle carousel job started - Scheduled Mode (Jumat/Sabtu/Minggu 20:00 WIB)")
    while True:
        next_time = next_friday_saturday_sunday_8pm()
        wait_seconds = (next_time - datetime.now()).total_seconds()
        logger.info(f"Next angle carousel post: {next_time.strftime('%Y-%m-%d %H:%M')} ({next_time.strftime('%A')})")
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        try:
            run_angle_job()
        except Exception as e:
            logger.error(f"Angle carousel job gagal: {e}")
        time.sleep(60)  # jaga-jaga biar gak ke-trigger 2x di menit yang sama


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scheduled", action="store_true", help="Jalankan mode otomatis Jum/Sab/Min 20:00 WIB")
    args = parser.parse_args()

    if args.scheduled:
        scheduled_loop()
    else:
        try:
            run_angle_job()
        except Exception as e:
            logger.exception(f"Angle carousel job gagal: {e}")
            sys.exit(1)
