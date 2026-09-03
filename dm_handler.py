"""dm_handler.py - BARU
Auto-reply DM yang minta rekomendasi film.
"""

import os, requests, random, time
from tmdb_client import search_movie, get_movie_details

IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
GRAPH_BASE = "https://graph.facebook.com/v20.0"

DM_RESPONSES = [
    "Halo! 🎬 Berikut rekomendasi film untukmu:",
    "Wah, lagi cari film nih? Coba ini! 🍿",
    "Rekomendasi spesial untukmu! ⭐",
    "Film ini cocok buat kamu! 🎥",
]

FOLLOW_UP_QUESTIONS = [
    "Mau genre apa lagi? Komen aja! 💬",
    "Ada film favorit kamu? Bisa request loh! 👇",
    "Follow biar dapet rekomendasi tiap hari! 📌",
]


def get_pending_dms():
    """Ambil DM yang belum dibalas."""
    # Note: Instagram Graph API Basic Display tidak support read DM
    # Butuh Instagram Business API yang lebih advanced
    # Ini adalah placeholder untuk integrasi dengan webhook/API yang sesuai
    return []


def send_dm(user_id, message):
    """Kirim DM ke user."""
    # Note: Mengirim DM via Graph API butuh permissions khusus
    # Placeholder untuk implementasi
    url = f"{GRAPH_BASE}/me/messages"
    payload = {
        "recipient": {"id": user_id},
        "message": {"text": message},
        "access_token": IG_ACCESS_TOKEN,
    }
    try:
        r = requests.post(url, json=payload, timeout=30)
        return r.status_code == 200
    except:
        return False


def generate_movie_recommendation(genre=None, year=None):
    """Generate rekomendasi film."""
    # Placeholder - integrate dengan tmdb_client
    movies = [
        {"title": "The Love Hypothesis", "year": 2024, "genre": "Romance"},
        {"title": "Inception", "year": 2010, "genre": "Sci-Fi"},
        {"title": "Parasite", "year": 2019, "genre": "Thriller"},
    ]
    if genre:
        movies = [m for m in movies if genre.lower() in m["genre"].lower()]
    return random.choice(movies) if movies else movies[0]


def process_pending_dms():
    """Proses semua DM yang pending."""
    dms = get_pending_dms()

    for dm in dms:
        user_id = dm.get("sender_id")
        message = dm.get("text", "").lower()

        # Parse request
        genre = None
        if any(g in message for g in ["romance", "romantis", "love"]):
            genre = "Romance"
        elif any(g in message for g in ["action", "aksi", "perang"]):
            genre = "Action"
        elif any(g in message for g in ["horror", "horor", "seram"]):
            genre = "Horror"
        elif any(g in message for g in ["comedy", "komedi", "lucu"]):
            genre = "Comedy"

        # Generate rekomendasi
        rec = generate_movie_recommendation(genre=genre)

        # Build response
        response = f"{random.choice(DM_RESPONSES)}\n\n"
        response += f"🎬 {rec['title']} ({rec['year']})\n"
        response += f"Genre: {rec['genre']}\n\n"
        response += random.choice(FOLLOW_UP_QUESTIONS)

        # Kirim
        send_dm(user_id, response)
        time.sleep(random.randint(5, 15))  # Anti-ban delay

    return len(dms)
