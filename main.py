"""
main.py (versi Termux)
Dijalankan sekali per eksekusi lewat cron Termux (jadwal 06:00 & 19:00 WIB).
Tidak ada server yang nyala terus -- cron yang atur jadwalnya.

Alur: pilih film random -> generate video slideshow (ffmpeg) -> push ke GitHub
buat dapat URL publik (jsDelivr) -> publish ke Instagram Reels.
"""

import os
import sys
import random
import uuid
import argparse
import logging

from dotenv import load_dotenv

load_dotenv()

from tmdb_client import get_random_movie, get_movie_details, get_movie_backdrops, build_trivia_facts
from video_builder import build_slideshow
from caption_generator import build_trivia_caption, build_guess_caption
from git_publisher import publish_video_to_github, cleanup_old_video
from ig_publisher import publish_reel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("ig-movie-bot")

MEDIA_DIR = os.path.join(os.path.dirname(__file__), "media")
os.makedirs(MEDIA_DIR, exist_ok=True)


def run_post_job(content_type=None):
    content_type = content_type or random.choice(["trivia", "guess"])
    logger.info(f"Mulai job posting, tipe: {content_type}")

    movie = get_random_movie(pool="mixed")
    details = get_movie_details(movie["id"])
    images = get_movie_backdrops(movie["id"])
    title = details.get("title", "Unknown")
    logger.info(f"Film terpilih: {title}")

    filename = f"{uuid.uuid4().hex}.mp4"
    output_path = os.path.join(MEDIA_DIR, filename)

    if content_type == "trivia":
        build_slideshow(images, output_path, mode="trivia")
        facts = build_trivia_facts(details)
        caption = build_trivia_caption(title, facts)
    else:
        build_slideshow(images, output_path, mode="guess", title_text=title)
        caption = build_guess_caption(title)

    logger.info("Video selesai dibuat, push ke GitHub...")
    video_url = publish_video_to_github(output_path, filename)
    logger.info(f"URL publik: {video_url}")

    logger.info("Publish ke Instagram...")
    result = publish_reel(video_url, caption)
    logger.info(f"Berhasil publish: {result}")

    # Bersihkan file lokal & di repo biar gak numpuk
    os.remove(output_path)
    cleanup_old_video(filename)

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--type", choices=["trivia", "guess"], default=None,
        help="Paksa tipe konten tertentu, default random"
    )
    args = parser.parse_args()

    try:
        run_post_job(content_type=args.type)
    except Exception as e:
        logger.exception(f"Job gagal: {e}")
        sys.exit(1)
