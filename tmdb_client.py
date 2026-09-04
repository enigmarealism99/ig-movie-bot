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

    Filter konten: exclude adult content, exclude film exploitation/obscure
    (vote_count rendah sering korelasi sama poster/backdrop yang gak pantas),
    dan exclude genre Horror (18930) yang gambarnya sering gore/ekstrem.
    """
    if pool == "mixed":
        pool = random.choice(["korea", "western"])

    base_params = {
        "sort_by": "popularity.desc",
        "page": random.randint(1, 5),
        "include_adult": "false",
        "vote_count.gte": 100,  # exclude film obscure/exploitation, hanya film yang cukup dikenal
        "without_genres": "27",  # exclude genre Horror (poster/backdrop sering gore/ekstrem)
    }

    if pool == "korea":
        params = {**base_params, "with_original_language": "ko"}
    else:
        params = {**base_params, "with_original_language": "en"}

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


def search_movie(query, limit=5):
    """
    Cari film berdasarkan judul/kata kunci (dipakai dm_handler.py buat
    balas DM user yang nanya soal film tertentu).
    Return list dict film mentah dari TMDB (id, title, overview, dst).
    """
    data = _get("/search/movie", {"query": query, "language": "id-ID"})
    results = data.get("results", [])
    return results[:limit]


def get_actor_trivia():
    """
    Ambil aktor populer random dari TMDB, plus foto profil (portrait, cocok
    langsung buat frame vertikal, gak perlu letterbox kayak backdrop film)
    dan beberapa fakta menarik. Return dict: name, images, facts.
    """
    page = random.randint(1, 5)
    data = _get("/person/popular", {"page": page})
    results = data.get("results", [])
    if not results:
        raise RuntimeError("TMDB tidak mengembalikan aktor, cek API key / parameter")
    person = random.choice(results)
    person_id = person["id"]

    details = _get(f"/person/{person_id}", {"append_to_response": "combined_credits"})
    images_data = _get(f"/person/{person_id}/images")

    profiles = images_data.get("profiles", [])
    profiles.sort(key=lambda x: x.get("vote_average", 0), reverse=True)
    chosen = profiles[:5] if profiles else []
    images = [f"{IMG_BASE}{p['file_path']}" for p in chosen]
    if not images and details.get("profile_path"):
        images = [f"{IMG_BASE}{details['profile_path']}"]
    if not images:
        raise RuntimeError(f"Tidak ada foto untuk person_id {person_id}")

    facts = []
    if details.get("birthday"):
        facts.append(f"Lahir: {details['birthday']}")
    if details.get("place_of_birth"):
        facts.append(f"Asal: {details['place_of_birth']}")
    if details.get("known_for_department"):
        facts.append(f"Dikenal sebagai: {details['known_for_department']}")

    known_for = details.get("combined_credits", {}).get("cast", [])
    known_for_sorted = sorted(known_for, key=lambda x: x.get("popularity", 0), reverse=True)[:3]
    titles = [c.get("title") or c.get("name") for c in known_for_sorted if c.get("title") or c.get("name")]
    if titles:
        facts.append(f"Dikenal lewat: {', '.join(titles)}")

    bio = details.get("biography", "")
    if bio:
        snippet = bio[:200].rsplit(" ", 1)[0] + "..." if len(bio) > 200 else bio
        facts.append(snippet)

    if not facts:
        facts = ["Salah satu aktor populer di industri film."]

    return {
        "name": details.get("name", "Unknown"),
        "images": images,
        "facts": facts,
    }


GENRE_IDS = {
    "action": 28, "comedy": 35, "drama": 18, "horror": 27,
    "thriller": 53, "romance": 10749, "scifi": 878, "animation": 16,
    "fantasy": 14, "crime": 80,
}

# Genre yang gambarnya berisiko ekstrem -- carousel jenis ini pakai POSTER
# resmi aja (bukan backdrop/scene still) biar visualnya tetap aman
SENSITIVE_GENRES = {"horror", "thriller", "crime"}


def _movie_poster_url(movie):
    if movie.get("poster_path"):
        return f"{IMG_BASE}{movie['poster_path']}"
    return None


def get_upcoming_movies(limit=5):
    """Film yang belum rilis, buat carousel 'coming soon'."""
    from datetime import date
    today = date.today().isoformat()
    data = _get("/discover/movie", {
        "sort_by": "popularity.desc",
        "primary_release_date.gte": today,
        "include_adult": "false",
    })
    results = [m for m in data.get("results", []) if _movie_poster_url(m)]
    return results[:limit]


def get_top_by_genre(genre_name, limit=5):
    """
    Top film by genre tertentu (misal 'horror terbaik'). Genre sensitif
    otomatis dibatasi pakai vote_count tinggi biar yang muncul film
    mainstream yang dikenal luas, bukan exploitation/obscure.
    """
    genre_id = GENRE_IDS.get(genre_name.lower())
    if not genre_id:
        raise ValueError(f"Genre '{genre_name}' gak dikenal, pilihan: {list(GENRE_IDS.keys())}")

    min_votes = 500 if genre_name.lower() in SENSITIVE_GENRES else 200
    data = _get("/discover/movie", {
        "with_genres": genre_id,
        "sort_by": "vote_average.desc",
        "vote_count.gte": min_votes,
        "include_adult": "false",
    })
    results = [m for m in data.get("results", []) if _movie_poster_url(m)]
    return results[:limit]


def get_budget_flops(limit=5, pool_size=20):
    """
    Film budget besar tapi revenue kurang dari budget (box office flop).
    TMDB discover gak support filter budget langsung, jadi ambil pool film
    populer dulu, baru disaring satu-satu lewat detail.
    """
    candidates = []
    for page in range(1, 3):
        data = _get("/discover/movie", {
            "sort_by": "popularity.desc", "page": page,
            "include_adult": "false", "vote_count.gte": 200,
        })
        candidates.extend(data.get("results", []))
        if len(candidates) >= pool_size:
            break

    flops = []
    for movie in candidates[:pool_size]:
        details = get_movie_details(movie["id"])
        budget = details.get("budget", 0)
        revenue = details.get("revenue", 0)
        if budget >= 50_000_000 and 0 < revenue < budget and _movie_poster_url(details):
            flops.append(details)
        if len(flops) >= limit:
            break

    return flops


def get_weekly_top(limit=5):
    """Film terpopuler minggu ini (trending)."""
    data = _get("/trending/movie/week")
    results = [m for m in data.get("results", []) if _movie_poster_url(m) and not m.get("adult")]
    return results[:limit]
