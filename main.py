"""main.py (FINAL ALL-IN-ONE)
Bot Instagram Film - Termux Edition
Fitur: Trivia, Guess, Auto-Reply DM, Komentar Pancingan, Anti-Ban, Scheduled Random
"""

import os
import sys
import random
import uuid
import argparse
import logging
import time
import threading
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

from tmdb_client import get_random_movie, get_movie_details, get_movie_backdrops, build_trivia_facts, get_actor_trivia
from video_builder import build_slideshow
from caption_generator import build_trivia_caption, build_guess_caption, build_actor_caption
from git_publisher import publish_video_to_github, cleanup_old_video
from ig_publisher import publish_reel
from dm_handler import process_pending_dms
from comment_bot import add_bait_comment
from anti_ban import human_delay, random_posting_time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ig-movie-bot")

MEDIA_DIR = os.path.join(os.path.dirname(__file__), "media")
os.makedirs(MEDIA_DIR, exist_ok=True)


def detect_source(movie_details):
    """Deteksi asal film dari data TMDB."""
    countries = movie_details.get("origin_country", [])
    if "ID" in countries:
        return "indonesia"
    if "KR" in countries:
        return "korea"
    if "JP" in countries:
        return "japan"
    if "IN" in countries:
        return "india"
    if "CN" in countries or "TW" in countries or "HK" in countries:
        return "china"
    return "western"


def run_post_job(content_type=None, actor_mode=False):
    """Jalankan 1 job posting."""
    content_type = content_type or random.choice(["trivia", "guess"])

    # Anti-ban: random delay sebelum mulai
    human_delay(min_sec=5, max_sec=30)

    logger.info(f"Mulai job posting, tipe: {content_type}")

    if actor_mode:
        # Mode trivia aktor
        actor_data = get_actor_trivia()
        title = actor_data["name"]
        images = actor_data["images"]
        facts = actor_data["facts"]
        source = "western"  # Default, bisa di-enhance
        trivia_text = " ".join(facts[:3])
        if len(trivia_text) > 300:
            trivia_text = trivia_text[:297].rsplit(' ', 1)[0] + "..."

        filename = f"actor_{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(MEDIA_DIR, filename)

        build_slideshow(images, output_path, mode="trivia", title_text=title, trivia_text=trivia_text)
        caption = build_actor_caption(title, facts)
    else:
        # Mode film biasa
        movie = get_random_movie(pool="mixed")
        details = get_movie_details(movie["id"])
        images = get_movie_backdrops(movie["id"])
        title = details.get("title", "Unknown")
        source = detect_source(details)

        logger.info(f"Film terpilih: {title} ({source})")

        filename = f"{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(MEDIA_DIR, filename)

        if content_type == "trivia":
            facts = build_trivia_facts(details)
            trivia_text = " ".join(facts) if isinstance(facts, list) else str(facts)
            if len(trivia_text) > 300:
                trivia_text = trivia_text[:297].rsplit(' ', 1)[0] + "..."

            build_slideshow(images, output_path, mode="trivia", title_text=title, trivia_text=trivia_text)
            caption = build_trivia_caption(title, facts, source)
        else:
            build_slideshow(images, output_path, mode="guess", title_text=title)
            caption = build_guess_caption(title, source)

    # Simpan ke Downloads HP
    try:
        import shutil
        download_path = f"/sdcard/Download/{filename}"
        shutil.copy2(output_path, download_path)
        logger.info(f"Video juga disimpan di: {download_path}")
    except Exception as e:
        logger.warning(f"Tidak bisa copy ke Downloads: {e}")

    # Push ke GitHub
    logger.info("Push ke GitHub...")
    video_url = publish_video_to_github(output_path, filename)
    logger.info(f"URL publik: {video_url}")

    # Anti-ban: delay sebelum publish
    human_delay(min_sec=10, max_sec=45)

    # Publish ke Instagram
    logger.info("Publish ke Instagram...")
    result = publish_reel(video_url, caption, local_video_path=output_path)
    media_id = result.get("id")
    logger.info(f"Berhasil publish: {media_id}")

    # Komentar pancingan otomatis (5-15 menit setelah post)
    if media_id:
        def delayed_comment():
            human_delay(min_sec=300, max_sec=900)  # 5-15 menit
            add_bait_comment(media_id)
        threading.Thread(target=delayed_comment, daemon=True).start()

    # Cleanup
    os.remove(output_path)
    cleanup_old_video(filename)

    return result


def run_dm_handler():
    """Proses DM yang masuk."""
    try:
        process_pending_dms()
    except Exception as e:
        logger.warning(f"DM handler error: {e}")


def scheduled_loop():
    """Loop jadwal posting otomatis dengan waktu random."""
    logger.info("Bot film IG started - Scheduled Mode")

    while True:
        now = datetime.now()

        # Hitung waktu post berikutnya (random dalam range)
        next_post_time = random_posting_time()
        wait_seconds = (next_post_time - now).total_seconds()

        if wait_seconds > 0:
            logger.info(f"Next post at: {next_post_time.strftime('%Y-%m-%d %H:%M')}")
            time.sleep(wait_seconds)

        # Posting
        try:
            content_type = random.choice(["trivia", "guess"])
            actor_mode = random.random() < 0.2  # 20% chance post aktor
            run_post_job(content_type=content_type, actor_mode=actor_mode)
        except Exception as e:
            logger.error(f"Post failed: {e}")
            # Anti-ban: backoff jika error
            time.sleep(random.randint(1800, 3600))  # 30-60 menit

        # Proses DM setelah posting
        run_dm_handler()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["trivia", "guess"], default=None, help="Paksa tipe konten")
    parser.add_argument("--actor", action="store_true", help="Mode trivia aktor")
    parser.add_argument("--scheduled", action="store_true", help="Jalankan scheduled loop")
    parser.add_argument("--dm-only", action="store_true", help="Hanya proses DM")
    args = parser.parse_args()

    if args.dm_only:
        run_dm_handler()
    elif args.scheduled:
        scheduled_loop()
    else:
        try:
            run_post_job(content_type=args.type, actor_mode=args.actor)
        except Exception as e:
            logger.exception(f"Job gagal: {e}")
            sys.exit(1)
