"""comment_bot.py - BARU
Auto-comment (bait) untuk trigger engagement.
"""

import random, time
from ig_publisher import post_comment
from caption_generator import get_bait_comment


def add_bait_comment(media_id, delay=True):
    """Tambah komentar pancingan ke post."""
    if delay:
        time.sleep(random.randint(1, 5))

    comment = get_bait_comment()
    try:
        result = post_comment(media_id, comment)
        print(f"✅ Bait comment posted: {comment[:50]}...")
        return result
    except Exception as e:
        print(f"❌ Gagal post comment: {e}")
        return None


def auto_reply_comments(media_id, keywords=None):
    """Auto-reply komentar yang mengandung keyword."""
    from ig_publisher import get_recent_comments, reply_to_comment

    if not keywords:
        keywords = ["bagus", "keren", "wow", "mantap", "rekomendasi", "nonton"]

    comments = get_recent_comments(media_id, limit=20)

    replies = {
        "bagus": "Iya nih, filmnya emang bagus banget! 🌟",
        "keren": "Setuju! Behind the scenes-nya juga keren! 🎬",
        "wow": "Fakta-faktanya bikin wow kan? 😱",
        "mantap": "Mantap! Save post ini buat referensi nonton! 📌",
        "rekomendasi": "Mau rekomendasi lain? DM aja! 💬",
        "nonton": "Udah nonton belum? Komen pengalamanmu! 🍿",
    }

    replied_ids = set()

    for comment in comments:
        cid = comment.get("id")
        text = comment.get("text", "").lower()

        if cid in replied_ids:
            continue

        for keyword in keywords:
            if keyword in text:
                reply_text = replies.get(keyword, "Thanks for commenting! 🙏")
                try:
                    reply_to_comment(cid, reply_text)
                    replied_ids.add(cid)
                    time.sleep(random.randint(3, 8))
                    break
                except:
                    pass

    return len(replied_ids)
