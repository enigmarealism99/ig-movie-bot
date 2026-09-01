"""
caption_generator.py
Susun caption Instagram untuk 2 tipe konten: trivia card & guess-the-movie.
"""

import random

TRIVIA_HOOKS = [
    "Tau gak sih fakta ini soal \"{title}\"? \U0001F440",
    "Trivia time! \"{title}\" ternyata... \U0001F3AC",
    "Sebelum nonton \"{title}\", cek fakta ini dulu \U0001F447",
]

GUESS_HOOKS = [
    "Tebak judul film dari potongan gambar ini di kolom komentar! \U0001F914",
    "Cuma butuh 1 scene buat nebak filmnya? Coba deh \U0001F440",
    "Siapa yang bisa tebak sebelum reveal terakhir? \U0001F447",
]

HASHTAG_POOL = [
    "#movierecommendation", "#filmkorea", "#hollywoodmovie", "#trivia",
    "#guesstheMovie", "#movienight", "#koreanmovie", "#westernmovie",
    "#reels", "#movietrivia",
]


def build_trivia_caption(title, facts, source="korea"):
    hook = random.choice(TRIVIA_HOOKS).format(title=title)
    body = "\n".join(f"\u2022 {f}" for f in facts[:5])
    tags = " ".join(random.sample(HASHTAG_POOL, 5))
    return f"{hook}\n\n{body}\n\n{tags}"


def build_guess_caption(title, source="korea"):
    hook = random.choice(GUESS_HOOKS)
    reveal_note = "Jawabannya ada di akhir video \U0001F447"
    tags = " ".join(random.sample(HASHTAG_POOL, 5))
    return f"{hook}\n\n{reveal_note}\n\nJudul: {title}\n\n{tags}"
