"""anti_ban.py - BARU
Strategi anti-ban Instagram: random delay, human-like behavior, backoff.
"""

import random, time
from datetime import datetime, timedelta


# Jadwal posting yang "manusiawi" (bukan exact time)
POSTING_RANGES = [
    (6, 8),    # Pagi: 06:00-08:00
    (11, 13),  # Siang: 11:00-13:00
    (18, 20),  # Sore: 18:00-20:00
    (20, 22),  # Malam: 20:00-22:00
]

DAILY_POST_LIMIT = 3  # Max post per hari


def human_delay(min_sec=5, max_sec=60):
    """Delay random untuk simulasi behavior manusia."""
    delay = random.randint(min_sec, max_sec)
    print(f"⏳ Human delay: {delay}s...")
    time.sleep(delay)
    return delay


def random_posting_time():
    """Generate waktu posting random dalam range yang manusiawi."""
    now = datetime.now()

    # Pilih range waktu
    hour_range = random.choice(POSTING_RANGES)
    target_hour = random.randint(hour_range[0], hour_range[1])
    target_minute = random.randint(0, 59)
    target_second = random.randint(0, 59)

    target = now.replace(hour=target_hour, minute=target_minute, second=target_second, microsecond=0)

    # Kalau sudah lewat, pindah ke besok
    if target <= now:
        target += timedelta(days=1)

    return target


def should_post_today(post_count_today):
    """Cek apakah masih boleh post hari ini."""
    if post_count_today >= DAILY_POST_LIMIT:
        print(f"⚠️ Daily limit reached ({DAILY_POST_LIMIT} posts)")
        return False

    # Random chance untuk skip (10%)
    if random.random() < 0.1:
        print("🎲 Random skip hari ini (anti-pattern)")
        return False

    return True


def exponential_backoff(attempt, base_delay=60):
    """Backoff eksponensial saat error."""
    delay = base_delay * (2 ** attempt) + random.randint(0, 30)
    print(f"⏳ Backoff: {delay}s (attempt {attempt+1})")
    time.sleep(delay)
    return delay


def random_user_agent():
    """Random user agent untuk request."""
    agents = [
        "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36",
    ]
    return random.choice(agents)


def simulate_typing(text, wpm=40):
    """Simulasi typing speed manusia."""
    chars = len(text)
    seconds = (chars / 5) / (wpm / 60)  # Rough estimate
    time.sleep(seconds)
    return seconds
