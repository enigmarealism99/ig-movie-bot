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
import requests
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

from tmdb_client import (
    get_random_movie, get_movie_details, get_movie_backdrops, build_trivia_facts,
    get_actor_trivia, get_upcoming_korean, get_horror_vs_pair, get_weekly_top, get_trailer_url,
)
from video_builder import build_slideshow
from caption_generator import (
    build_trivia_caption, build_guess_caption, build_actor_caption,
    build_bocoran_caption, build_polling_caption, build_vs_caption, build_trailer_caption,
)
from git_publisher import publish_video_to_github, cleanup_old_video
from ig_publisher import publish_reel
from dm_handler import process_pending_dms
from comment_bot import add_bait_comment
from anti_ban import human_delay, random_posting_time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("onair-korea-tv")

MEDIA_DIR = os.path.join(os.path.dirname(__file__), "media")
os.makedirs(MEDIA_DIR, exist_ok=True)

# ---------- WA / FB fanout config ----------
WA_ENDPOINT = os.environ.get("WA_ENDPOINT", "http://localhost:3000/send-to-channel")
WA_CHANNEL_JID = os.environ.get("WA_CHANNEL_JID", "120363428543568849@newsletter")
WA_ENABLED = os.environ.get("WA_ENABLED", "true").lower() != "false"
WA_CHANNEL_INVITE_LINK = os.environ.get("WA_CHANNEL_INVITE_LINK", "")

FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
GRAPH_API_VERSION = "v25.0"

# Jadwal harian: jam paling ramai audience (WIB) - jenis kontennya diputar
# terpisah dari jam (lihat CONTENT_ROTATION), jadi nambah jenis baru tinggal
# nambah 1 baris di pool ini, gak perlu utak-atik jam.
CONTENT_SLOT_TIMES = [(7, 0), (12, 30), (19, 30)]
CONTENT_ROTATION = ["bocoran", "polling", "link_fb", "trailer"]
_rotation_state = {"index": 0}

OUTRO_LABELS = {
    "bocoran": "Bocoran film & series baru",
    "polling": "Polling seru: vote pilihanmu",
    "link_fb": "Video VS lengkap horor Korea",
    "trailer": "Trailer terbaru + link nonton lengkap",
}

FB_RECENT_VIDEOS = []          # max 5 video_id terakhir, buat sasaran auto-reply komentar
FB_REPLIED_COMMENT_IDS = set()  # biar gak balas komentar yang sama 2x


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


def send_to_whatsapp_video(video_url, caption=""):
    """Kirim video yang sama ke Saluran WhatsApp lewat wa-channel-bot (index.js)."""
    if not WA_ENABLED:
        return
    try:
        payload = {"channelJid": WA_CHANNEL_JID, "text": caption, "videoUrl": video_url}
        resp = requests.post(WA_ENDPOINT, json=payload, timeout=30)
        resp.raise_for_status()
        logger.info("WA video post success")
    except Exception as e:
        logger.error(f"WA video post failed: {e}")


def post_reel_to_fb(video_url, caption):
    """Publish video ke FB Page sebagai Reels, 3 tahap: start -> transfer (file_url) -> finish."""
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        logger.error("FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN belum di-set di environment.")
        return {"error": "missing_credentials"}

    base = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{FB_PAGE_ID}/video_reels"
    try:
        start = requests.post(
            base, data={"upload_phase": "start", "access_token": FB_PAGE_ACCESS_TOKEN}, timeout=30
        ).json()
        video_id, upload_url = start["video_id"], start["upload_url"]

        transfer = requests.post(
            upload_url,
            headers={
                "Authorization": f"OAuth {FB_PAGE_ACCESS_TOKEN}",
                "offset": "0",
                "file_url": video_url,
            },
            timeout=60,
        )
        if not transfer.ok:
            logger.error(f"FB transfer gagal: {transfer.status_code} {transfer.text}")
            return {"error": f"transfer_failed: {transfer.text}"}

        finish = requests.post(base, params={
            "access_token": FB_PAGE_ACCESS_TOKEN,
            "video_id": video_id,
            "upload_phase": "finish",
            "video_state": "PUBLISHED",
            "description": caption,
        }, timeout=30).json()
        finish["video_id"] = video_id
        logger.info(f"FB Reels post success: {video_id}")
        return finish
    except Exception as e:
        logger.error(f"FB Reels post gagal: {e}")
        return {"error": str(e)}


def get_fb_permalink(video_id):
    """Ambil link permanen video FB - dipakai buat CTA di caption IG/WA (khusus link_fb)."""
    try:
        r = requests.get(
            f"https://graph.facebook.com/{GRAPH_API_VERSION}/{video_id}",
            params={"fields": "permalink_url", "access_token": FB_PAGE_ACCESS_TOKEN},
            timeout=15,
        ).json()
        path = r.get("permalink_url")
        return f"https://facebook.com{path}" if path else None
    except Exception as e:
        logger.error(f"Gagal ambil FB permalink: {e}")
        return None


def register_recent_fb_video(video_id):
    if not video_id:
        return
    FB_RECENT_VIDEOS.append(video_id)
    del FB_RECENT_VIDEOS[:-5]


def poll_fb_comments_for_wa_invite():
    """Cek komentar di video FB terbaru, balas otomatis kalau ada kata 'link' -
    dipakai buat narik orang gabung Channel WA."""
    if not WA_CHANNEL_INVITE_LINK:
        return
    for video_id in FB_RECENT_VIDEOS:
        try:
            resp = requests.get(
                f"https://graph.facebook.com/{GRAPH_API_VERSION}/{video_id}/comments",
                params={"fields": "id,message", "access_token": FB_PAGE_ACCESS_TOKEN},
                timeout=15,
            ).json()
            for c in resp.get("data", []):
                cid = c.get("id")
                msg = (c.get("message") or "").lower()
                if not cid or cid in FB_REPLIED_COMMENT_IDS or "link" not in msg:
                    continue
                reply = f"Gabung Channel WA buat update drama tiap hari: {WA_CHANNEL_INVITE_LINK}"
                requests.post(
                    f"https://graph.facebook.com/{GRAPH_API_VERSION}/{cid}/comments",
                    data={"message": reply, "access_token": FB_PAGE_ACCESS_TOKEN},
                    timeout=15,
                )
                FB_REPLIED_COMMENT_IDS.add(cid)
                logger.info(f"Auto-reply WA invite ke comment {cid}")
        except Exception as e:
            logger.error(f"Gagal poll komentar FB video {video_id}: {e}")


def comment_poll_loop():
    """Loop background, cek komentar FB tiap 15 menit (Termux gak punya webhook publik)."""
    while True:
        try:
            poll_fb_comments_for_wa_invite()
        except Exception as e:
            logger.error(f"Comment poll loop error: {e}")
        time.sleep(900)


def get_next_slot_label(current_kind):
    """Teks outro CTA: kasih tau jenis konten berikutnya di rotasi."""
    idx = CONTENT_ROTATION.index(current_kind) if current_kind in CONTENT_ROTATION else -1
    nxt_kind = CONTENT_ROTATION[(idx + 1) % len(CONTENT_ROTATION)]
    return f"{OUTRO_LABELS[nxt_kind]}\nnantikan di postingan berikutnya!"


def next_rotation_kind():
    """Ambil jenis konten berikutnya dari CONTENT_ROTATION secara berurutan
    (bukan random) - biar semua jenis kepakai rata, gak ada yang jarang muncul."""
    kind = CONTENT_ROTATION[_rotation_state["index"] % len(CONTENT_ROTATION)]
    _rotation_state["index"] += 1
    return kind


def run_fanout_job(content_kind=None):
    """Job posting baru: 1 video digenerate sekali, di-fanout ke FB -> WA -> IG.
    Rotasi 3 jenis: bocoran (info upcoming), polling (2 film random), link_fb (VS horror mahal-murah)."""
    content_kind = content_kind or random.choice(CONTENT_ROTATION)
    human_delay(min_sec=5, max_sec=30)
    logger.info(f"Mulai job OnAir Korea TV, jenis: {content_kind}")

    filename = f"{content_kind}_{uuid.uuid4().hex}.mp4"
    output_path = os.path.join(MEDIA_DIR, filename)
    outro_text = get_next_slot_label(content_kind)
    title_a = title_b = None

    if content_kind == "bocoran":
        items = get_upcoming_korean(limit=10)
        if not items:
            logger.warning("Gak ada film upcoming Korea, skip job ini.")
            return
        movie = random.choice(items)
        details = get_movie_details(movie["id"])
        title_a = details.get("title", "Unknown")
        images = get_movie_backdrops(movie["id"])
        build_slideshow(
            images, output_path, mode="trivia", title_text=title_a,
            trivia_text="Segera hadir! Masuk watchlist kamu sekarang \U0001F440",
            outro_text=outro_text,
        )
        fb_caption = wa_caption = ig_caption = build_bocoran_caption(title_a, details.get("overview", ""))

    elif content_kind == "polling":
        movie_a, movie_b = get_random_movie(pool="mixed"), get_random_movie(pool="mixed")
        detail_a, detail_b = get_movie_details(movie_a["id"]), get_movie_details(movie_b["id"])
        title_a, title_b = detail_a.get("title", "Unknown"), detail_b.get("title", "Unknown")
        images_a, images_b = get_movie_backdrops(movie_a["id"]), get_movie_backdrops(movie_b["id"])
        build_slideshow(
            images_a + images_b, output_path, mode="vs",
            title_text=title_a, title_text_b=title_b,
            trivia_text="Mana yang lebih worth ditonton? Vote di komentar!",
            split_index=len(images_a), outro_text=outro_text,
        )
        fb_caption = wa_caption = ig_caption = build_polling_caption(title_a, title_b)

    elif content_kind == "trailer":
        items = get_weekly_top(limit=10)
        if not items:
            logger.warning("Gak ada film trending, skip job ini.")
            return
        movie = random.choice(items)
        details = get_movie_details(movie["id"])
        title_a = details.get("title", "Unknown")
        trailer_url = get_trailer_url(details)
        images = get_movie_backdrops(movie["id"])
        build_slideshow(
            images, output_path, mode="trivia", title_text=title_a,
            trivia_text="Udah nonton trailernya? Link lengkap di caption!",
            outro_text=outro_text,
        )
        fb_caption = wa_caption = ig_caption = build_trailer_caption(title_a, trailer_url)

    else:  # link_fb
        detail_a, detail_b = get_horror_vs_pair()
        title_a, title_b = detail_a.get("title", "Unknown"), detail_b.get("title", "Unknown")
        images_a, images_b = get_movie_backdrops(detail_a["id"]), get_movie_backdrops(detail_b["id"])
        build_slideshow(
            images_a + images_b, output_path, mode="vs",
            title_text=title_a, title_text_b=title_b,
            trivia_text="Budget beda jauh, tapi yang mana lebih serem?",
            split_index=len(images_a), outro_text=outro_text,
        )
        fb_caption = build_vs_caption(title_a, title_b)  # tanpa link FB dulu, diisi setelah publish
        wa_caption = ig_caption = fb_caption

    logger.info("Push video ke GitHub...")
    video_url = publish_video_to_github(output_path, filename)
    logger.info(f"URL publik: {video_url}")

    # ---------- Fanout: FB -> WA -> IG ----------
    fb_permalink = None
    try:
        fb_result = post_reel_to_fb(video_url, fb_caption)
        video_id = fb_result.get("video_id")
        if video_id:
            register_recent_fb_video(video_id)
            fb_permalink = get_fb_permalink(video_id)
        else:
            logger.error(f"FB post gagal: {fb_result}")
    except Exception as e:
        logger.error(f"FB post error: {e}")

    if content_kind == "link_fb":
        wa_caption = ig_caption = build_vs_caption(title_a, title_b, fb_link=fb_permalink)

    try:
        send_to_whatsapp_video(video_url, wa_caption)
    except Exception as e:
        logger.error(f"WA post error: {e}")

    human_delay(min_sec=10, max_sec=45)
    try:
        result = publish_reel(video_url, ig_caption, local_video_path=output_path)
        media_id = result.get("id")
        logger.info(f"Berhasil publish IG: {media_id}")
        if media_id:
            def delayed_comment():
                human_delay(min_sec=300, max_sec=900)
                add_bait_comment(media_id)
            threading.Thread(target=delayed_comment, daemon=True).start()
    except Exception as e:
        logger.error(f"IG post error: {e}")

    os.remove(output_path)
    cleanup_old_video(filename)


def next_scheduled_slot():
    """Cari jam slot berikutnya dari CONTENT_SLOT_TIMES, plus jitter kecil (anti-ban)."""
    now = datetime.now()
    today_slots = [
        now.replace(hour=h, minute=m, second=0, microsecond=0)
        for h, m in CONTENT_SLOT_TIMES
    ]
    for slot_time in today_slots:
        if slot_time > now:
            jitter = timedelta(minutes=random.randint(-5, 10))
            return slot_time + jitter
    tomorrow = today_slots[0] + timedelta(days=1)
    jitter = timedelta(minutes=random.randint(-5, 10))
    return tomorrow + jitter


def onair_scheduled_loop():
    """Mode otomatis permanen: 3 slot jam/hari, jenis kontennya diputar
    berurutan dari CONTENT_ROTATION (independen dari jam slotnya).
    Sekalian jalanin comment_poll_loop di background buat auto-reply FB."""
    logger.info("OnAir Korea TV started - Scheduled Mode")
    threading.Thread(target=comment_poll_loop, daemon=True).start()

    while True:
        next_time = next_scheduled_slot()
        content_kind = next_rotation_kind()
        wait_seconds = (next_time - datetime.now()).total_seconds()
        if wait_seconds > 0:
            logger.info(f"Next post ({content_kind}) at: {next_time.strftime('%Y-%m-%d %H:%M')}")
            time.sleep(wait_seconds)
        try:
            run_fanout_job(content_kind=content_kind)
        except Exception as e:
            logger.error(f"Post failed ({content_kind}): {e}")
            time.sleep(random.randint(1800, 3600))
        run_dm_handler()


def run_dm_handler():
    """Proses DM yang masuk."""
    try:
        process_pending_dms()
    except Exception as e:
        logger.warning(f"DM handler error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["trivia", "guess"], default=None,
                         help="[lama] Paksa tipe konten trivia/guess, post ke IG doang")
    parser.add_argument("--actor", action="store_true", help="[lama] Mode trivia aktor, IG doang")
    parser.add_argument("--content-kind", choices=["bocoran", "polling", "link_fb", "trailer"], default=None,
                         help="Jalankan 1 job baru (fanout IG+WA+FB), buat testing manual")
    parser.add_argument("--scheduled", action="store_true",
                         help="Mode otomatis: 3 slot/hari (07:00 bocoran, 12:30 polling, 19:30 link_fb), fanout ke IG+WA+FB")
    parser.add_argument("--dm-only", action="store_true", help="Hanya proses DM")
    args = parser.parse_args()

    if args.dm_only:
        run_dm_handler()
    elif args.scheduled:
        onair_scheduled_loop()
    elif args.content_kind:
        try:
            run_fanout_job(content_kind=args.content_kind)
        except Exception as e:
            logger.exception(f"Job gagal: {e}")
            sys.exit(1)
    elif args.type or args.actor:
        try:
            run_post_job(content_type=args.type, actor_mode=args.actor)
        except Exception as e:
            logger.exception(f"Job gagal: {e}")
            sys.exit(1)
    else:
        try:
            run_fanout_job()
        except Exception as e:
            logger.exception(f"Job gagal: {e}")
            sys.exit(1)
