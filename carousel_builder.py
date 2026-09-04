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


def build_trivia_carousel(title, poster_url, facts, output_dir):
    """Slide 1 = poster + judul, slide berikutnya 1 fakta per slide."""
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    # Slide 1: poster + judul film
    cover_img = _download_image(poster_url)
    cover = _blurred_letterbox(cover_img)
    draw = ImageDraw.Draw(cover)
    font_title = _load_font(FONT_BOLD, 56)
    _draw_wrapped_text(draw, title, 70, font_title, width_chars=20)
    font_tag = _load_font(FONT_REGULAR, 34)
    _draw_wrapped_text(draw, "Fakta Menarik \u2192", HEIGHT - 100, font_tag, width_chars=30)
    cover_path = os.path.join(output_dir, "slide_1_cover.jpg")
    cover.save(cover_path, quality=90)
    paths.append(cover_path)

    # Slide fakta
    font_fact = _load_font(FONT_BOLD, 46)
    for i, fact in enumerate(facts[:4]):
        img = Image.new("RGB", (WIDTH, HEIGHT), (18, 18, 26))
        draw = ImageDraw.Draw(img)
        font_num = _load_font(FONT_BOLD, 40)
        draw.text((60, 60), f"{i+1:02d}", font=font_num, fill=(120, 120, 140))
        _draw_wrapped_text(draw, fact, HEIGHT // 2 - 100, font_fact, width_chars=26)
        path = os.path.join(output_dir, f"slide_{i+2}.jpg")
        img.save(path, quality=90)
        paths.append(path)

    return paths


def build_list_carousel(items, list_title, output_dir):
    """
    items: list of dict {rank, title, image_url, subtitle}
    Slide 1 = judul list, slide berikutnya 1 film per slide (rank + poster + info).
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    cover = Image.new("RGB", (WIDTH, HEIGHT), (15, 15, 25))
    draw = ImageDraw.Draw(cover)
    font_huge = _load_font(FONT_BOLD, 64)
    _draw_wrapped_text(draw, list_title, HEIGHT // 2 - 80, font_huge, width_chars=18)
    font_swipe = _load_font(FONT_REGULAR, 32)
    _draw_wrapped_text(draw, "Geser untuk lihat semua \u2192", HEIGHT - 100, font_swipe, width_chars=30)
    cover_path = os.path.join(output_dir, "slide_0_cover.jpg")
    cover.save(cover_path, quality=90)
    paths.append(cover_path)

    for item in items:
        img = _download_image(item["image_url"])
        canvas = _blurred_letterbox(img)
        draw = ImageDraw.Draw(canvas)
        font_rank = _load_font(FONT_BOLD, 88)
        draw.text((40, 40), f"#{item['rank']}", font=font_rank, fill="white",
                   stroke_width=5, stroke_fill="black")
        font_title = _load_font(FONT_BOLD, 46)
        y = _draw_wrapped_text(draw, item["title"], HEIGHT - 190, font_title, width_chars=24)
        if item.get("subtitle"):
            font_sub = _load_font(FONT_REGULAR, 32)
            _draw_wrapped_text(draw, item["subtitle"], y + 10, font_sub, width_chars=34)

        path = os.path.join(output_dir, f"slide_{item['rank']}.jpg")
        canvas.save(path, quality=90)
        paths.append(path)

    return paths
