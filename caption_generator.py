"""caption_generator.py - FINAL
Caption Instagram untuk trivia film, aktor, & guess-the-movie.
"""

import random

TRIVIA_HOOKS = [
    "🎬 Tau gak sih fakta ini soal \"{title}\"?",
    "🍿 Trivia time! \"{title}\" ternyata...",
    "🎥 Sebelum nonton \"{title}\", cek fakta ini dulu!",
    "💡 Fakta menarik dari \"{title}\" yang jarang diketahui!",
    "🔥 Film \"{title}\" punya cerita di balik layar yang keren!",
]

ACTOR_HOOKS = [
    "🌟 Tau gak sih tentang {name}?",
    "🎭 Fakta menarik soal {name}!",
    "⭐ Aktor {name} ternyata...",
    "🎬 Di balik layar {name}...",
]

GUESS_HOOKS = [
    "🤔 Tebak judul film dari potongan gambar ini!",
    "🎬 Cuma butuh 1 scene buat nebak filmnya? Coba deh!",
    "👀 Siapa yang bisa tebak sebelum reveal? Komen di bawah!",
    "🍿 Clue: Film populer ini pernah trending worldwide!",
    "🎯 Tebak filmnya! Hint ada di visualnya~",
]

CTA_POOL = [
    "Follow untuk trivia film tiap hari! 🎬",
    "Tag teman yang harus tau fakta ini! 👇",
    "Save post ini buat referensi nonton nanti! 📌",
    "Komen film apa yang mau di-trivia-in next! 💬",
    "Share ke story biar temanmu ikutan tau! 📤",
]

BAIT_COMMENTS = [
    "Siapa yang udah nonton ini? 🙋‍♂️",
    "Film ini worth it gak sih menurut kalian? 🤔",
    "Aku baru tau fakta no. 3! 😱",
    "Kalian tim nonton di bioskop atau streaming? 🍿",
    "Next film apa yang mau di-trivia-in? Komen! 👇",
    "Fakta paling keren yang mana menurut kalian? 💬",
    "Aktor/aktris favorit kalian di film ini siapa? 🌟",
    "Rating berapa nih film menurut kalian? ⭐",
]

HASHTAG_POOL = [
    "#movierecommendation", "#filmkorea", "#hollywoodmovie", "#trivia",
    "#guessthemovie", "#movienight", "#koreanmovie", "#westernmovie",
    "#reels", "#movietrivia", "#filmbarurelease", "#moviefacts",
    "#filmrecommendation", "#movielover", "#sinopsisfilm",
    "#netflixindonesia", "#disneyplus", "#filmviral", "#cinematrivia",
    "#filmindonesia", "#filmasia", "#drakor", "#bollywood", "#japanmovie",
    "#chinesemovie", "#moviequiz", "#filmterbaru", "#nontonbareng",
    "#actortrivia", "#behindthescenes", "#filmtrivia", "#moviebuff",
]

SOURCE_HASHTAGS = {
    "indonesia": ["#filmindonesia", "#moviendonesia", "#filmasliindonesia", "#sinemaindonesia"],
    "korea": ["#filmkorea", "#koreanmovie", "#drakor", "#kdrama"],
    "japan": ["#filmjepang", "#japanmovie", "#japanesefilm", "#animeliveaction"],
    "india": ["#bollywood", "#filmindia", "#indianmovie", "#bollywoodmovie"],
    "china": ["#filmchina", "#chinesemovie", "#mandarinfilm", "#cdrama"],
    "western": ["#hollywoodmovie", "#westernmovie", "#boxoffice", "#hollywood"],
}


def _truncate_facts(facts, max_chars=600):
    result, cur = [], 0
    for f in facts:
        line = f"• {f}"
        if cur + len(line) > max_chars:
            break
        result.append(f)
        cur += len(line) + 1
    return result


def build_trivia_caption(title, facts, source="western"):
    facts = _truncate_facts(facts)
    hook = random.choice(TRIVIA_HOOKS).format(title=title)
    body = "\n".join(f"• {f}" for f in facts[:5])
    cta = random.choice(CTA_POOL)

    base = ["#movietrivia", "#trivia", "#reels"]
    base.extend(SOURCE_HASHTAGS.get(source, SOURCE_HASHTAGS["western"])[:2])
    extra = random.sample([t for t in HASHTAG_POOL if t not in base], 3)
    tags = " ".join(base + extra)

    caption = f"{hook}\n\n{body}\n\n{cta}\n\n{tags}"
    print(f"📊 Panjang caption: {len(caption)} char")
    return caption


def build_actor_caption(name, facts, source="western"):
    facts = _truncate_facts(facts)
    hook = random.choice(ACTOR_HOOKS).format(name=name)
    body = "\n".join(f"• {f}" for f in facts[:5])
    cta = random.choice(CTA_POOL)

    base = ["#actortrivia", "#trivia", "#reels", "#behindthescenes"]
    extra = random.sample([t for t in HASHTAG_POOL if t not in base], 4)
    tags = " ".join(base + extra)

    return f"{hook}\n\n{body}\n\n{cta}\n\n{tags}"


def build_guess_caption(title, source="western"):
    hook = random.choice(GUESS_HOOKS)
    cta = random.choice([
        "Komen jawabanmu di bawah! 👇",
        "Tebak dulu baru scroll ke bawah! 😏",
        "Jangan curang! Komen sebelum liat reveal! 🙈",
    ])
    reveal = "💡 Reveal: Slide terakhir!"

    base = ["#guessthemovie", "#reels", "#moviequiz"]
    base.extend(SOURCE_HASHTAGS.get(source, SOURCE_HASHTAGS["western"])[:2])
    extra = random.sample([t for t in HASHTAG_POOL if t not in base], 3)
    tags = " ".join(base + extra)

    return f"{hook}\n\n{cta}\n\n{reveal}\n\n{tags}"


def get_bait_comment():
    """Ambil komentar pancingan random."""
    return random.choice(BAIT_COMMENTS)
