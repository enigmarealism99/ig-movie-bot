"""
main.py
Entry point. Jalan sebagai web service kecil (biar Railway kasih public URL buat
hosting video sementara) + scheduler APScheduler yang trigger posting 2x sehari
(06:00 & 19:00 WIB), tipe konten (trivia / guess) dipilih random tiap slot.
"""

import os
import random
import uuid
import logging
from datetime import datetime

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from tmdb_client import get_random_movie, get_movie_details, get_movie_backdrops, build_trivia_facts
from video_builder import build_slideshow
from caption_generator import build_trivia_caption, build_guess_caption
from ig_publisher import publish_reel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ig-movie-bot")

APP_PUBLIC_URL = os.getenv("APP_PUBLIC_URL")  # contoh: https://ig-movie-bot.up.railway.app
MEDIA_DIR = os.path.join(os.path.dirname(__file__), "media")
os.makedirs(MEDIA_DIR, exist_ok=True)

app = FastAPI()
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")


@app.get("/")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


def run_post_job(content_type=None):
    """Job utama: pilih film -> generate video -> publish ke IG."""
    content_type = content_type or random.choice(["trivia", "guess"])
    logger.info(f"Menjalankan job posting, tipe: {content_type}")

    try:
        movie = get_random_movie(pool="mixed")
        details = get_movie_details(movie["id"])
        images = get_movie_backdrops(movie["id"])
        title = details.get("title", "Unknown")

        filename = f"{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(MEDIA_DIR, filename)

        if content_type == "trivia":
            build_slideshow(images, output_path, mode="trivia")
            facts = build_trivia_facts(details)
            caption = build_trivia_caption(title, facts)
        else:
            build_slideshow(images, output_path, mode="guess", title_text=title)
            caption = build_guess_caption(title)

        if not APP_PUBLIC_URL:
            raise RuntimeError("APP_PUBLIC_URL belum diset di environment variables")

        video_url = f"{APP_PUBLIC_URL}/media/{filename}"
        result = publish_reel(video_url, caption)
        logger.info(f"Berhasil publish: {result}")
        return result

    except Exception as e:
        logger.exception(f"Job posting gagal: {e}")
        raise


def start_scheduler():
    tz = pytz.timezone("Asia/Jakarta")
    scheduler = BackgroundScheduler(timezone=tz)
    scheduler.add_job(run_post_job, CronTrigger(hour=6, minute=0, timezone=tz))
    scheduler.add_job(run_post_job, CronTrigger(hour=19, minute=0, timezone=tz))
    scheduler.start()
    logger.info("Scheduler aktif: posting jam 06:00 dan 19:00 WIB")
    return scheduler


@app.on_event("startup")
def on_startup():
    start_scheduler()


# Endpoint manual buat testing tanpa nunggu jadwal cron
@app.post("/test-post")
def test_post(content_type: str = None):
    result = run_post_job(content_type=content_type)
    return {"result": result}
