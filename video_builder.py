"""video_builder.py - FINAL
Bikin video Reels (1080x1920) dari backdrop TMDB.
Fix: zoom 1.1x, text overlay, TTS voiceover, format valid.
"""

import os, subprocess, tempfile, requests, textwrap, random, glob, asyncio

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

WIDTH, HEIGHT, FPS = 1080, 1920, 30
MUSIC_DIR = os.path.join(os.path.dirname(__file__), "music")

# Suara Indonesia yang natural (Edge TTS, gratis). Bisa ganti ke suara lain:
# id-ID-GadisNeural (perempuan) atau id-ID-ArdiNeural (laki-laki)
EDGE_VOICE = "id-ID-ArdiNeural"

FONT_PATHS = [
    os.path.join(os.path.dirname(__file__), "fonts", "Poppins-Bold.ttf"),
    "/system/fonts/Roboto-Bold.ttf",
    "/data/data/com.termux/files/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_PATH = next((fp for fp in FONT_PATHS if os.path.exists(fp)), None)


def _download_image(url, dest):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)
    return dest


async def _edge_tts_async(text, output_path, voice):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def _generate_tts(text, output_path, lang='id'):
    text = text[:300].rsplit('.', 1)[0] + '.' if len(text) > 300 else text

    # Coba Edge TTS dulu -- suaranya jauh lebih natural, gratis, gak perlu API key
    if EDGE_TTS_AVAILABLE:
        try:
            asyncio.run(_edge_tts_async(text, output_path, EDGE_VOICE))
            return True
        except Exception as e:
            print(f"Edge TTS error, fallback ke gTTS: {e}")

    # Fallback ke gTTS kalau Edge TTS gagal (misal gak ada internet ke server MS)
    if GTTS_AVAILABLE:
        try:
            gTTS(text=text, lang=lang, slow=False).save(output_path)
            return True
        except Exception as e:
            print(f"TTS error: {e}")
            return False

    return False


def _pick_background_music():
    """Ambil 1 file musik random dari folder music/ kalau ada."""
    if not os.path.isdir(MUSIC_DIR):
        return None
    files = glob.glob(os.path.join(MUSIC_DIR, "*.mp3")) + glob.glob(os.path.join(MUSIC_DIR, "*.m4a"))
    return random.choice(files) if files else None


def _get_audio_duration(path):
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
               '-of', 'default=noprint_wrappers=1:nokey=1', path]
        return float(subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout.strip())
    except:
        return None


def _build_single_frame(img, out, duration, trivia=None, title=None, zoom_in=True):
    frames = int(duration * FPS)
    z = "min(zoom+0.0008,1.12)" if zoom_in else "if(lte(zoom,1.0),1.12,max(1.001,zoom-0.0008))"

    # Teknik 'blurred letterbox': gambar ditampilkan UTUH di tengah (gak
    # dipotong), background blur dari gambar yang sama ngisi ruang kosong --
    # bukan upscale+crop paksa yang bikin gambar landscape kepotong sempit
    # ekstrem waktu dipaksa isi frame portrait 9:16.
    filter_complex = (
        f"split=2[bg][fg];"
        f"[bg]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},gblur=sigma=40,eq=brightness=-0.12[bgblur];"
        f"[fg]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease[fgfit];"
        f"[bgblur][fgfit]overlay=(W-w)/2:(H-h)/2[comp];"
        f"[comp]zoompan=z='{z}':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},format=yuv420p[zoomed]"
    )
    last = "zoomed"

    texts = []
    if title and FONT_PATH:
        st = title.replace("'", "\'").replace(":", "\:").replace(",", "\,")
        texts.append(f"drawtext=fontfile={FONT_PATH}:text='{st}':fontcolor=white:fontsize=56:borderw=4:bordercolor=black@0.8:x=(w-text_w)/2:y=80:line_spacing=8")
    if trivia and FONT_PATH:
        st = trivia.replace("'", "\'").replace(":", "\:").replace(",", "\,")
        wrapped = '\\n'.join(textwrap.wrap(st, width=30))
        texts.append(f"drawtext=fontfile={FONT_PATH}:text='{wrapped}':fontcolor=white:fontsize=36:borderw=3:bordercolor=black@0.8:x=(w-text_w)/2:y=h-280:line_spacing=6")

    for idx, txt_filter in enumerate(texts):
        new_label = f"txt{idx}"
        filter_complex += f";[{last}]{txt_filter}[{new_label}]"
        last = new_label

    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", img, "-filter_complex", filter_complex,
           "-map", f"[{last}]", "-t", str(duration), "-pix_fmt", "yuv420p", "-r", str(FPS), out]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ffmpeg error (clip): {result.stderr[-500:]}")
    return result.returncode == 0


def build_slideshow(urls, output_path, mode="trivia", title_text=None, trivia_text=None):
    if not urls:
        raise ValueError("image_urls kosong!")

    if not trivia_text and mode == "trivia":
        trivia_text = "Tahukah kamu? Film ini punya fakta menarik!"

    with tempfile.TemporaryDirectory() as tmpdir:
        imgs = []
        for i, url in enumerate(urls):
            dest = os.path.join(tmpdir, f"img_{i}.jpg")
            _download_image(url, dest)
            imgs.append(dest)

        n = len(imgs)
        total_dur = n * 3  # tanpa voiceover, durasi tetap 3 detik per gambar

        # Build clips
        clips = []
        for i, img in enumerate(imgs):
            clip_out = os.path.join(tmpdir, f"clip_{i}.mp4")
            dur = total_dur / n

            if mode == "guess" and i != n - 1:
                blurred = os.path.join(tmpdir, f"blur_{i}.jpg")
                subprocess.run(["ffmpeg", "-y", "-i", img, "-vf", f"gblur=sigma={max(20-i*6,5)}", blurred], capture_output=True)
                img = blurred

            if not _build_single_frame(img, clip_out, dur,
                                       trivia_text if mode=="trivia" else None,
                                       title_text if i==0 else None,
                                       i % 2 == 0):
                raise RuntimeError(f"Gagal build clip {i}")
            clips.append(clip_out)

        # Concat
        concat = os.path.join(tmpdir, "concat.txt")
        with open(concat, "w") as f:
            for c in clips:
                f.write(f"file '{c}'\n")

        silent = os.path.join(tmpdir, "silent.mp4")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat, "-c", "copy", silent], check=True, capture_output=True)

        # Audio: musik latar random (looped/trimmed ke durasi video), tanpa voiceover.
        # Kalau gak ada file musik, tetap kasih track senyap (Reels wajib ada audio track).
        music_path = _pick_background_music()

        if music_path:
            cmd = [
                "ffmpeg", "-y",
                "-i", silent,
                "-stream_loop", "-1", "-i", music_path,
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-pix_fmt", "yuv420p", "-r", str(FPS),
                "-af", "volume=0.6",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                "-shortest", "-movflags", "+faststart", output_path,
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-i", silent,
                "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-pix_fmt", "yuv420p", "-r", str(FPS),
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                "-shortest", "-movflags", "+faststart", output_path,
            ]

        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"Merge error: {r.stderr}")

        if not os.path.exists(output_path) or os.path.getsize(output_path) < 1000:
            raise RuntimeError("Output corrupt")

        print(f"Video selesai: {output_path} ({os.path.getsize(output_path)/1024/1024:.1f} MB)")
        return output_path
