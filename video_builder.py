"""
video_builder.py
Bikin video Reels (1080x1920, vertical) dari backdrop stills TMDB pakai efek Ken Burns (zoompan)
via ffmpeg. Tidak menggunakan potongan video asli film -- hanya still image resmi.
"""

import os
import subprocess
import tempfile
import requests

WIDTH, HEIGHT = 1080, 1920
SECONDS_PER_IMAGE = 3
FPS = 30
_CUSTOM_FONT = os.path.join(os.path.dirname(__file__), "fonts", "Poppins-Bold.ttf")
_FALLBACK_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_PATH = _CUSTOM_FONT if os.path.exists(_CUSTOM_FONT) else _FALLBACK_FONT


def _download_image(url, dest_path):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    with open(dest_path, "wb") as f:
        f.write(r.content)
    return dest_path


def _zoompan_filter(zoom_in=True):
    """Filter Ken Burns: perlahan zoom in atau zoom out selama durasi clip."""
    frames = SECONDS_PER_IMAGE * FPS
    if zoom_in:
        z_expr = f"min(zoom+0.0015,1.3)"
    else:
        z_expr = f"if(lte(zoom,1.0),1.3,max(1.001,zoom-0.0015))"
    return (
        f"scale={WIDTH*2}:{HEIGHT*2}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH*2}:{HEIGHT*2},"
        f"zoompan=z='{z_expr}':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
    )


def build_slideshow(image_urls, output_path, mode="trivia", title_text=None):
    """
    mode: 'trivia'  -> Ken Burns normal semua gambar
          'guess'   -> gambar pertama-pertama diblur berat, gambar terakhir jelas + title reveal
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        local_images = []
        for i, url in enumerate(image_urls):
            dest = os.path.join(tmpdir, f"img_{i}.jpg")
            _download_image(url, dest)
            local_images.append(dest)

        clip_paths = []
        for i, img in enumerate(local_images):
            clip_out = os.path.join(tmpdir, f"clip_{i}.mp4")
            is_last = i == len(local_images) - 1
            zoom_in = i % 2 == 0

            vf = _zoompan_filter(zoom_in=zoom_in)

            if mode == "guess" and not is_last:
                # Blur berat untuk gambar "tebak-tebakan", makin ke belakang makin jelas dikit
                blur_strength = max(25 - (i * 8), 8)
                vf += f",gblur=sigma={blur_strength}"

            if mode == "guess" and is_last and title_text:
                safe_title = title_text.replace("'", "\u2019").replace(":", "\\:")
                vf += (
                    f",drawtext=fontfile={FONT_PATH}:text='{safe_title}':"
                    f"fontcolor=white:fontsize=64:borderw=3:bordercolor=black:"
                    f"x=(w-text_w)/2:y=h-350"
                )

            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", img,
                "-vf", vf,
                "-t", str(SECONDS_PER_IMAGE),
                "-pix_fmt", "yuv420p",
                clip_out,
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            clip_paths.append(clip_out)

        # Gabungkan semua clip jadi satu video pakai concat demuxer
        concat_list = os.path.join(tmpdir, "concat.txt")
        with open(concat_list, "w") as f:
            for c in clip_paths:
                f.write(f"file '{c}'\n")

        cmd_concat = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list,
            "-c", "copy",
            output_path,
        ]
        subprocess.run(cmd_concat, check=True, capture_output=True)

    return output_path
