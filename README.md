# 🤖 IG Movie Bot - All-in-One

Bot Instagram auto-post film trivia, guess-the-movie, aktor trivia, auto-reply DM, komentar pancingan, anti-ban.

## 🚀 Fitur

- ✅ **Auto-Post Trivia Film** - Fakta menarik + voiceover TTS
- ✅ **Guess The Movie** - Tebak film dari scene blur
- ✅ **Aktor Trivia** - Fakta menarik tentang aktor
- ✅ **Auto-Reply DM** - Rekomendasi film via DM
- ✅ **Komentar Pancingan** - Auto-comment untuk trigger engagement
- ✅ **Anti-Ban** - Random delay, human-like behavior, daily limit
- ✅ **Source Detection** - Auto-detect ID/KR/JP/IN/CN/Western
- ✅ **Scheduled Random** - Posting otomatis dengan waktu random

## 📱 Setup Termux

```bash
pkg update && pkg install git python ffmpeg
pip install -r requirements.txt
```

## ⚙️ Environment

```bash
cp .env.example .env
# Edit .env dengan API keys
```

## 🎬 Cara Pakai

```bash
# Post trivia sekali
python main.py --type trivia

# Post guess-the-movie
python main.py --type guess

# Post aktor trivia
python main.py --type trivia --actor

# Scheduled mode (loop otomatis)
python main.py --scheduled

# Hanya proses DM
python main.py --dm-only
```

## ⏰ Cron (Jadwal Otomatis)

```bash
crontab -e

# Jalankan scheduled mode setiap jam
0 * * * * cd ~/ig-movie-bot && python main.py --scheduled
```

## 📁 Struktur File

```
ig-movie-bot/
├── main.py              # Entry point
├── video_builder.py     # Generate video Reels
├── caption_generator.py # Generate caption
├── ig_publisher.py      # Publish ke Instagram
├── git_publisher.py     # Push ke GitHub
├── tmdb_client.py       # Integrasi TMDB API
├── dm_handler.py        # Auto-reply DM
├── comment_bot.py       # Komentar pancingan
├── anti_ban.py          # Strategi anti-ban
├── media/               # Folder video
├── fonts/               # Font custom (opsional)
├── .env                 # Environment variables
└── requirements.txt     # Dependencies
```

## 🛡️ Anti-Ban Strategy

- Random delay 5-60 detik antar aksi
- Waktu posting random dalam range (tidak exact)
- Daily limit: max 3 post/hari
- 10% chance skip hari (anti-pattern)
- Exponential backoff saat error
- Human-like typing simulation

## 📝 Catatan

- `tmdb_client.py` adalah placeholder. Ganti dengan implementasi asli kamu.
- DM handler butuh Instagram Business API permissions.
- Font custom: taruh di folder `fonts/Poppins-Bold.ttf`.
