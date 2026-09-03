"""tmdb_client.py - PLACEHOLDER
Integrasi dengan TMDB API. Ganti dengan file asli kamu.
"""

import os, requests, random

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"


def get_random_movie(pool="mixed"):
    """Ambil film random dari TMDB."""
    # Placeholder - implementasi asli di file kamu
    return {"id": 550, "title": "Fight Club"}


def get_movie_details(movie_id):
    """Ambil detail film."""
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {"api_key": TMDB_API_KEY, "language": "id-ID"}
    r = requests.get(url, params=params, timeout=30)
    return r.json()


def get_movie_backdrops(movie_id):
    """Ambil backdrop images."""
    url = f"{BASE_URL}/movie/{movie_id}/images"
    params = {"api_key": TMDB_API_KEY}
    r = requests.get(url, params=params, timeout=30)
    data = r.json()
    backdrops = data.get("backdrops", [])
    urls = [f"https://image.tmdb.org/t/p/w1280{b['file_path']}" for b in backdrops[:3]]
    return urls if urls else ["https://via.placeholder.com/1080x1920"]


def build_trivia_facts(details):
    """Build fakta trivia dari detail film."""
    facts = []
    if details.get("tagline"):
        facts.append(details["tagline"])
    if details.get("overview"):
        facts.append(details["overview"][:150] + "...")
    if details.get("budget", 0) > 0:
        facts.append(f"Budget: ${details['budget']:,}")
    if details.get("runtime"):
        facts.append(f"Durasi: {details['runtime']} menit")
    if details.get("release_date"):
        facts.append(f"Rilis: {details['release_date']}")
    return facts if facts else ["Film ini punya cerita menarik!"]


def get_actor_trivia():
    """Ambil trivia aktor random. Placeholder."""
    return {
        "name": "Tom Hanks",
        "images": ["https://via.placeholder.com/1080x1920"],
        "facts": [
            "Pernah menang Oscar 2x berturut-turut",
            "Voice actor Woody di Toy Story",
            "Dikenal sebagai aktor paling baik hati di Hollywood"
        ]
    }


def search_movie(query):
    """Cari film berdasarkan query."""
    url = f"{BASE_URL}/search/movie"
    params = {"api_key": TMDB_API_KEY, "query": query, "language": "id-ID"}
    r = requests.get(url, params=params, timeout=30)
    return r.json().get("results", [])
