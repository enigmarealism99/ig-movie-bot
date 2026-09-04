"""
carousel_job.py
Job posting carousel (multi-gambar) ke Instagram -- terpisah dari main.py
(yang urus Reels) biar gak ada risiko ganggu alur yang udah jalan.

Jalankan: python carousel_job.py --type trivia
          python carousel_job.py --type list
          python carousel_job.py  (random pilih salah satu)
"""

import os
import sys
import random
import uuid
import argparse
import logging

from dotenv import load_dotenv
load_dotenv()

from tmdb_client import (
    get_random_movie, get_movie_details, build_trivia_facts,
    get_upcoming_movies, get_top_by_genre, get_budget_flops, get_weekly_top,
    _movie_poster_url, GENRE_IDS, SENSITIVE_GENRES,
)
from carousel_builder import build_trivia_carousel, build_list_carousel
from caption_generator import build_carousel_trivia_caption, build_carousel_list_caption
from git_publisher import publish_images_to_github, cleanup_files
from ig_publisher import publish_carousel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("carousel-job")

MEDIA_DIR = os.path.join(os.path.dirname(__file__), "media")
os.makedirs(MEDIA_DIR, exist_ok=True)


LIST_SOURCES = [
    ("weekly_top", "Top 5 Film Trending Minggu Ini"),
    ("upcoming", "Film yang Akan Datang"),
    ("genre_horror", "Horror Terbaik"),
    ("genre_action", "Action Terbaik"),
    ("flops", "Box Office Flop Termahal"),
]


def _get_list_items(source_key, list_title):
    if source_key == "weekly_top":
        movies = get_weekly_top(limit=5)
    elif source_key == "upcoming":
        movies = get_upcoming_movies(limit=5)
    elif source_key == "flops":
        movies = get_budget_flops(limit=5)
    elif source_key.startswith("genre_"):
        genre = source_key.replace("genre_", "")
        movies = get_top_by_genre(genre, limit=5)
    else:
        raise ValueError(f"Source gak dikenal: {source_key}")

    items = []
    for i, m in enumerate(movies):
        title = m.get("title", "Unknown")
        subtitle = None
        if source_key == "flops":
            budget = m.get("budget", 0)
            revenue = m.get("revenue", 0)
            subtitle = f"Budget ${budget:,} - Revenue ${revenue:,}"
        elif m.get("vote_average"):
            subtitle = f"Rating {m['vote_average']}/10"

        items.append({
            "rank": i + 1,
            "title": title,
            "image_url": _movie_poster_url(m),
            "subtitle": subtitle,
        })
    return items


def run_carousel_trivia():
    movie = get_random_movie(pool="mixed")
    details = get_movie_details(movie["id"])
    title = details.get("title", "Unknown")
    poster_url = _movie_poster_url(details)
    if not poster_url:
        raise RuntimeError("Film ini gak punya poster, skip")

    facts = build_trivia_facts(details)
    logger.info(f"Carousel trivia: {title}")

    slide_dir = os.path.join(MEDIA_DIR, f"carousel_{uuid.uuid4().hex}")
    slide_paths = build_trivia_carousel(title, poster_url, facts, slide_dir)

    filenames = [f"{os.path.basename(slide_dir)}_{os.path.basename(p)}" for p in slide_paths]
    pairs = list(zip(slide_paths, filenames))

    urls = publish_images_to_github(pairs)
    caption = build_carousel_trivia_caption(title, facts)

    result = publish_carousel(urls, caption)

    cleanup_files(filenames)
    for p in slide_paths:
        os.remove(p)
    os.rmdir(slide_dir)

    return result


def run_carousel_list():
    source_key, list_title = random.choice(LIST_SOURCES)
    logger.info(f"Carousel list: {list_title} ({source_key})")

    items = _get_list_items(source_key, list_title)
    items = [it for it in items if it["image_url"]]
    if len(items) < 2:
        raise RuntimeError(f"Data gak cukup buat carousel list ({source_key})")

    slide_dir = os.path.join(MEDIA_DIR, f"carousel_{uuid.uuid4().hex}")
    slide_paths = build_list_carousel(items, list_title, slide_dir)

    filenames = [f"{os.path.basename(slide_dir)}_{os.path.basename(p)}" for p in slide_paths]
    pairs = list(zip(slide_paths, filenames))

    urls = publish_images_to_github(pairs)
    caption = build_carousel_list_caption(list_title)

    result = publish_carousel(urls, caption)

    cleanup_files(filenames)
    for p in slide_paths:
        os.remove(p)
    os.rmdir(slide_dir)

    return result


def run_carousel_job(content_type=None):
    content_type = content_type or random.choice(["trivia", "list"])
    logger.info(f"Mulai carousel job, tipe: {content_type}")

    if content_type == "trivia":
        return run_carousel_trivia()
    else:
        return run_carousel_list()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["trivia", "list"], default=None)
    args = parser.parse_args()

    try:
        run_carousel_job(content_type=args.type)
    except Exception as e:
        logger.exception(f"Carousel job gagal: {e}")
        sys.exit(1)
