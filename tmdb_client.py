"""
tmdb_client.py
Ambil data film Korea + Barat dari TMDB: daftar populer, detail, dan gambar backdrop.
"""

import os
import random
import requests

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/original"


def _get(path, params=None):
    params = params or {}
    params["api_key"] = TMDB_API_KEY
    r = requests.get(f"{TMDB_BASE}{path}", params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def get_random_movie(pool="mixed"):
    """
    pool: 'korea', 'western', atau 'mixed' (default, random pilih salah satu)
    Return dict film dasar (belum termasuk images/credits).
    """
    if pool == "mixed":
        pool = random.choice(["korea", "western"])

    if pool == "korea":
        params = {
            "with_original_language": "ko",
            "sort_by": "popularity.desc",
            "page": random.randint(1, 5),
        }
    else:
        params = {
            "with_original_language": "en",
            "sort_by": "popularity.desc",
            "page": random.randint(1, 5),
        }

    data = _get("/discover/movie", params)
    results = data.get("results", [])
    if not results:
        raise RuntimeError("TMDB tidak mengembalikan hasil, cek API key / parameter")
    return random.choice(results)


def get_movie_details(movie_id):
    """Detail lengkap + credits (cast) dalam satu request."""
    return _get(f"/movie/{movie_id}", {"append_to_response": "credits"})


def get_movie_backdrops(movie_id, min_count=3, max_count=5):
    """
    Ambil beberapa backdrop image (still resmi TMDB, bukan capture video).
    Return list URL gambar full resolution.
    """
    data = _get(f"/movie/{movie_id}/images")
    backdrops = data.get("backdrops", [])
    if not backdrops:
        # fallback ke poster kalau backdrop kosong
        posters = data.get("posters", [])
        backdrops = posters

    if not backdrops:
        raise RuntimeError(f"Tidak ada gambar untuk movie_id {movie_id}")

    # Urutkan berdasarkan vote_average TMDB (kualitas gambar yang dipilih user lain)
    backdrops.sort(key=lambda x: x.get("vote_average", 0), reverse=True)
    chosen = backdrops[:max_count]
    if len(chosen) < min_count:
        chosen = backdrops  # ambil semua yang ada kalau kurang dari minimum

    return [f"{IMG_BASE}{b['file_path']}" for b in chosen]


def build_trivia_facts(details):
    """
    Susun beberapa fakta menarik dari data TMDB untuk caption/overlay trivia card.
    Return list string pendek, siap pakai.
    """
    facts = []

    if details.get("tagline"):
        facts.append(f"Tagline: \"{details['tagline']}\"")

    if details.get("budget"):
        facts.append(f"Budget produksi: ${details['budget']:,}")

    if details.get("revenue"):
        facts.append(f"Pendapatan box office: ${details['revenue']:,}")

    if details.get("runtime"):
        facts.append(f"Durasi: {details['runtime']} menit")

    if details.get("vote_average"):
        facts.append(f"Rating TMDB: {details['vote_average']}/10")

    cast = details.get("credits", {}).get("cast", [])[:3]
    if cast:
        names = ", ".join(c["name"] for c in cast)
        facts.append(f"Pemeran utama: {names}")

    director = next(
        (c["name"] for c in details.get("credits", {}).get("crew", [])
         if c.get("job") == "Director"),
        None,
    )
    if director:
        facts.append(f"Sutradara: {director}")

    return facts
