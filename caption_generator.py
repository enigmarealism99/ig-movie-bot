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


ACTOR_HOOKS = [
    "Tau gak sih fakta menarik soal {name}? \U0001F31F",
    "{name} ternyata punya cerita menarik di baliknya \U0001F3AC",
    "Kenalan yuk lebih dalam sama {name} \U0001F447",
]

ACTOR_HASHTAG_POOL = [
    "#aktor", "#aktris", "#hollywood", "#trivia", "#behindthescenes",
    "#movienight", "#reels", "#didyouknow", "#celebritytrivia", "#filmfacts",
]


def build_actor_caption(name, facts):
    hook = random.choice(ACTOR_HOOKS).format(name=name)
    body = "\n".join(f"\u2022 {f}" for f in facts[:5])
    tags = " ".join(random.sample(ACTOR_HASHTAG_POOL, 5))
    return f"{hook}\n\n{body}\n\n{tags}"


BAIT_COMMENTS = [
    "Siapa yang udah pernah nonton ini? Komen di bawah! \U0001F447",
    "Tag temen yang wajib nonton film ini \U0001F440",
    "Setuju gak sama fakta ini? Kasih tau pendapat kalian \U0001F447",
    "Drop emoji kalau kalian suka genre ini! \U0001F3AC",
    "Menurut kalian gimana? Komen ya \U0001F447",
]


def get_bait_comment():
    """Komentar pancingan (engagement bait) buat dipost otomatis setelah publish."""
    return random.choice(BAIT_COMMENTS)


CAROUSEL_TRIVIA_HOOKS = [
    "Fakta-fakta {title} yang jarang diketahui \U0001F440 Geser \u2192",
    "Yuk kenalan lebih dalam sama \"{title}\" \U0001F3AC",
    "{title}: berapa banyak fakta ini yang kamu tau? \U0001F447",
]

CAROUSEL_LIST_HOOKS = [
    "{list_title} \U0001F447 Save biar gak lupa!",
    "{list_title} versi kita \U0001F3AC Setuju gak?",
    "{list_title} \u2014 mana favorit kamu? Komen di bawah!",
]


def build_carousel_trivia_caption(title, facts):
    hook = random.choice(CAROUSEL_TRIVIA_HOOKS).format(title=title)
    tags = " ".join(random.sample(HASHTAG_POOL, 5))
    return f"{hook}\n\n{tags}"


def build_carousel_list_caption(list_title):
    hook = random.choice(CAROUSEL_LIST_HOOKS).format(list_title=list_title)
    tags = " ".join(random.sample(HASHTAG_POOL, 5))
    return f"{hook}\n\n{tags}"


# ---------- Konten WA/FB: bocoran, polling, VS (link_fb) ----------

BOCORAN_HOOKS = [
    "Bocoran duluan! \"{title}\" bakal segera rilis \U0001F440",
    "Belum rilis tapi udah wajib masuk watchlist: \"{title}\" \U0001F3AC",
    "Coming soon: \"{title}\". Siap-siap masukin jadwal nonton \U0001F447",
]


def build_bocoran_caption(title, overview=""):
    hook = random.choice(BOCORAN_HOOKS).format(title=title)
    synopsis = (overview or "").strip()
    if len(synopsis) > 200:
        synopsis = synopsis[:197].rsplit(" ", 1)[0] + "..."
    tags = " ".join(random.sample(HASHTAG_POOL, 5))
    body = f"\n\n{synopsis}" if synopsis else ""
    return f"{hook}{body}\n\n{tags}"


POLLING_HOOKS = [
    "Tim \"{a}\" atau Tim \"{b}\"? Vote di komentar! \U0001F447",
    "\"{a}\" VS \"{b}\" — pilih salah satu, komen alasannya \U0001F440",
    "Mana yang lebih worth ditonton, \"{a}\" atau \"{b}\"?",
]


def build_polling_caption(title_a, title_b):
    hook = random.choice(POLLING_HOOKS).format(a=title_a, b=title_b)
    tags = " ".join(random.sample(HASHTAG_POOL, 5))
    return f"{hook}\n\n{tags}"


VS_HOOKS = [
    "\"{title_a}\" (budget besar) VS \"{title_b}\" (budget kecil) — tapi yang murah justru bikin merinding \U0001F631",
    "Horror mahal vs horror receh: \"{title_a}\" VS \"{title_b}\". Siapa sangka yang murah lebih serem?",
    "Budget beda jauh, tapi \"{title_b}\" justru lebih ngena dari \"{title_a}\" \U0001F480",
]

VS_CTA_TEMPLATES = [
    "Perbandingan lengkapnya ada di video FB kita \U0001F449 {fb_link}",
    "Nonton versi lengkap komparasinya di Facebook \U0001F447 {fb_link}",
]

VS_CTA_FALLBACK = "Nonton versi lengkap komparasinya di Facebook Page kita!"


def build_vs_caption(title_a, title_b, fb_link=None):
    hook = random.choice(VS_HOOKS).format(title_a=title_a, title_b=title_b)
    cta = random.choice(VS_CTA_TEMPLATES).format(fb_link=fb_link) if fb_link else VS_CTA_FALLBACK
    tags = " ".join(random.sample(HASHTAG_POOL, 5))
    return f"{hook}\n\n{cta}\n\n{tags}"
