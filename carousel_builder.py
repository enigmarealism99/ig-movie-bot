"""
carousel_builder.py
Generate slide carousel (gambar statis) buat Instagram carousel post.
Pakai PIL, bukan ffmpeg -- lebih ringan & cepat dari video Reels.
"""

import os
import textwrap
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

WIDTH, HEIGHT = 1080, 1350  # rasio 4:5 -- rasio carousel yang disarankan Instagram
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
FONT_BOLD = os.path.join(FONT_DIR, "Poppins-Bold.ttf")
FONT_REGULAR = os.path.join(FONT_DIR, "Poppins-Regular.ttf")
FALLBACK_FONT = "/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"


def _load_font(path, size):
    for candidate in (path, FALLBACK_FONT):
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _download_image(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")


def _blurred_letterbox(img):
    """Gambar utuh di tengah + background blur -- sama seperti teknik di video_builder.py."""
    bg_ratio = max(WIDTH / img.width, HEIGHT / img.height)
    bg = img.resize((int(img.width * bg_ratio) + 1, int(img.height * bg_ratio) + 1))
    left = (bg.width - WIDTH) // 2
    top = (bg.height - HEIGHT) // 2
    bg = bg.crop((left, top, left + WIDTH, top + HEIGHT))
    bg = bg.filter(ImageFilter.GaussianBlur(35))
    bg = ImageEnhance.Brightness(bg).enhance(0.55)

    fg_ratio = min(WIDTH / img.width, HEIGHT / img.height)
    fg = img.resize((int(img.width * fg_ratio), int(img.height * fg_ratio)))
    canvas = bg.copy()
    x = (WIDTH - fg.width) // 2
    y = (HEIGHT - fg.height) // 2
    canvas.paste(fg, (x, y))
    return canvas


def _draw_wrapped_text(draw, text, y, font, width_chars=30, fill="white", stroke_width=3, stroke_fill="black"):
    wrapped = textwrap.wrap(text, width=width_chars)
    line_height = font.size + 12
    for i, line in enumerate(wrapped):
        w = draw.textlength(line, font=font)
        x = (WIDTH - w) / 2
        draw.text((x, y + i * line_height), line, font=font, fill=fill,
                   stroke_width=stroke_width, stroke_fill=stroke_fill)
    return y + len(wrapped) * line_height


def _fullbleed_blur_bg(img, darken=0.45, blur=45):
    """
    Background dekoratif full-frame (crop-fill, BUKAN letterbox) -- buat cover
    slide / background fact slide, di mana gambar cuma jadi mood/tema, bukan
    konten utama yang harus utuh kelihatan.
    """
    ratio = max(WIDTH / img.width, HEIGHT / img.height)
    resized = img.resize((int(img.width * ratio) + 1, int(img.height * ratio) + 1))
    left = (resized.width - WIDTH) // 2
    top = (resized.height - HEIGHT) // 2
    cropped = resized.crop((left, top, left + WIDTH, top + HEIGHT))
    blurred = cropped.filter(ImageFilter.GaussianBlur(blur))
    return ImageEnhance.Brightness(blurred).enhance(darken)


def _add_gradient_overlay(img, position="bottom", strength=0.75):
    """Gradient gelap di atas/bawah gambar biar teks di atasnya tetap kebaca."""
    overlay = Image.new("L", (1, HEIGHT), 0)
    for y in range(HEIGHT):
        if position == "bottom":
            alpha = int(255 * strength * max(0, (y - HEIGHT * 0.35) / (HEIGHT * 0.65)))
        else:
            alpha = int(255 * strength * max(0, 1 - y / (HEIGHT * 0.5)))
        overlay.putpixel((0, y), alpha)
    overlay = overlay.resize((WIDTH, HEIGHT))
    black = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    img.paste(black, (0, 0), overlay)
    return img


def _accent_badge(draw, text, x, y, font, fg="white", bg=(230, 30, 60)):
    """Badge/pill kecil (kayak label) -- buat aksen visual biar gak polos."""
    padding_x, padding_y = 24, 12
    w = draw.textlength(text, font=font)
    h = font.size
    draw.rounded_rectangle(
        [x, y, x + w + padding_x * 2, y + h + padding_y * 2],
        radius=(h + padding_y * 2) // 2, fill=bg,
    )
    draw.text((x + padding_x, y + padding_y - 2), text, font=font, fill=fg)
    return h + padding_y * 2


GENRE_ACCENT_COLORS = {
    "horror": (180, 20, 20), "action": (230, 100, 20), "thriller": (150, 20, 60),
    "comedy": (240, 180, 20), "romance": (220, 60, 130), "drama": (60, 90, 200),
    "scifi": (30, 180, 200), "default": (230, 30, 60),
}


def build_trivia_carousel(title, poster_url, facts, output_dir):
    """Slide 1 = poster + judul (background full-bleed blur), slide berikutnya 1 fakta per slide (background sama, gak polos)."""
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    cover_img = _download_image(poster_url)

    # Slide 1: poster utuh (letterbox, biar poster kebaca jelas) + judul
    cover = _blurred_letterbox(cover_img)
    cover = _add_gradient_overlay(cover, position="bottom", strength=0.7)
    draw = ImageDraw.Draw(cover)
    font_badge = _load_font(FONT_BOLD, 30)
    _accent_badge(draw, "FAKTA MENARIK", 50, 60, font_badge, bg=GENRE_ACCENT_COLORS["default"])
    font_title = _load_font(FONT_BOLD, 58)
    _draw_wrapped_text(draw, title, HEIGHT - 260, font_title, width_chars=20)
    cover_path = os.path.join(output_dir, "slide_1_cover.jpg")
    cover.save(cover_path, quality=90)
    paths.append(cover_path)

    # Slide fakta: pakai background blur dari poster yang sama (bukan polos),
    # teks di atas gradient + card semi-transparan biar tetap kebaca
    bg_deco = _fullbleed_blur_bg(cover_img, darken=0.35, blur=55)
    font_fact = _load_font(FONT_BOLD, 44)
    for i, fact in enumerate(facts[:4]):
        img = bg_deco.copy().convert("RGB")
        img = _add_gradient_overlay(img, position="bottom", strength=0.6)
        img = _add_gradient_overlay(img, position="top", strength=0.35)
        draw = ImageDraw.Draw(img)
        font_num = _load_font(FONT_BOLD, 42)
        _accent_badge(draw, f"FAKTA {i+1}", 50, 60, font_num, bg=GENRE_ACCENT_COLORS["default"])
        _draw_wrapped_text(draw, fact, HEIGHT // 2 - 60, font_fact, width_chars=24)
        path = os.path.join(output_dir, f"slide_{i+2}.jpg")
        img.save(path, quality=90)
        paths.append(path)

    return paths


def build_list_carousel(items, list_title, output_dir, accent_key="default"):
    """
    items: list of dict {rank, title, image_url, subtitle}
    Slide 1 = judul list (background dari film #1, bukan polos), slide
    berikutnya 1 film per slide (rank + poster + info).
    accent_key: kunci warna aksen (lihat GENRE_ACCENT_COLORS), disesuaikan
    tema list-nya (misal 'horror' buat carousel Horror Terbaik).
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = []
    accent = GENRE_ACCENT_COLORS.get(accent_key, GENRE_ACCENT_COLORS["default"])

    # Cover: background dari poster item #1 (blur + gradient), bukan warna polos
    cover_source = _download_image(items[0]["image_url"])
    cover = _fullbleed_blur_bg(cover_source, darken=0.4, blur=40)
    cover = _add_gradient_overlay(cover, position="bottom", strength=0.75)
    cover = _add_gradient_overlay(cover, position="top", strength=0.3)
    draw = ImageDraw.Draw(cover)
    font_badge = _load_font(FONT_BOLD, 30)
    _accent_badge(draw, "TOP LIST", 50, 60, font_badge, bg=accent)
    font_huge = _load_font(FONT_BOLD, 66)
    _draw_wrapped_text(draw, list_title, HEIGHT - 320, font_huge, width_chars=16)
    font_swipe = _load_font(FONT_REGULAR, 32)
    _draw_wrapped_text(draw, "Geser untuk lihat semua \u2192", HEIGHT - 100, font_swipe, width_chars=30)
    cover_path = os.path.join(output_dir, "slide_0_cover.jpg")
    cover.save(cover_path, quality=90)
    paths.append(cover_path)

    for item in items:
        img = _download_image(item["image_url"])
        canvas = _blurred_letterbox(img)
        canvas = _add_gradient_overlay(canvas, position="bottom", strength=0.7)
        draw = ImageDraw.Draw(canvas)
        font_rank = _load_font(FONT_BOLD, 80)
        _accent_badge(draw, f"#{item['rank']}", 40, 40, font_rank, bg=accent)
        font_title = _load_font(FONT_BOLD, 46)
        y = _draw_wrapped_text(draw, item["title"], HEIGHT - 190, font_title, width_chars=24)
        if item.get("subtitle"):
            font_sub = _load_font(FONT_REGULAR, 32)
            _draw_wrapped_text(draw, item["subtitle"], y + 10, font_sub, width_chars=34)

        path = os.path.join(output_dir, f"slide_{item['rank']}.jpg")
        canvas.save(path, quality=90)
        paths.append(path)

    return paths
