# IG Movie Bot (Termux edition)

Bot posting otomatis ke Instagram Reels, 2x sehari (06:00 & 19:00 WIB), rotasi
random antara 2 tipe konten:
- **Trivia card** — fakta film dari TMDB (budget, cast, rating, dll)
- **Guess-the-movie** — backdrop di-blur bertahap, reveal judul di akhir

Sumber gambar: backdrop/still resmi dari TMDB (bukan capture video/trailer),
diolah jadi slideshow video dengan efek Ken Burns via ffmpeg.

Video hasil generate di-hosting gratis lewat GitHub + jsDelivr CDN (bukan
Railway) — cocok buat dijalankan penuh dari Termux tanpa biaya apapun.

## Setup di Termux

### 1. Install dependencies
```
pkg update -y && pkg upgrade -y
pkg install -y python ffmpeg git cronie
pip install -r requirements.txt --break-system-packages
```

### 2. Clone repo (kalau belum)
```
cd ~
git clone https://github.com/enigmarealism99/ig-movie-bot.git
cd ig-movie-bot
```
Kalau sudah pernah clone/upload manual sebelumnya, cukup `cd` ke foldernya
dan pastikan remote GitHub sudah benar (`git remote -v`).

### 3. Setup git credential (biar bisa push tanpa masukin password tiap kali)
```
git config --global user.email "email_kamu@example.com"
git config --global user.name "enigmarealism99"
git config --global credential.helper store
```
Push pertama kali akan minta username + **Personal Access Token** GitHub
(bukan password akun) — buat di github.com → Settings → Developer settings →
Personal access tokens → Generate new token (scope: `repo`). Setelah dimasukkan
sekali, tersimpan otomatis untuk push berikutnya.

### 4. Isi file `.env`
Copy `.env.example` jadi `.env`, isi sesuai kondisi kamu:
```
cp .env.example .env
nano .env
```
- `TMDB_API_KEY` — key TMDB yang sudah ada (bekas onairtalkbot)
- `IG_USER_ID` — sudah terisi: `17841480212098302`
- `IG_ACCESS_TOKEN` — long-lived token yang sudah kamu generate & simpan
- `GITHUB_USERNAME`, `GITHUB_REPO`, `GITHUB_BRANCH` — sudah terisi default

### 5. Test manual
```
python main.py --type trivia
```
Tunggu sampai selesai, cek Instagram — kalau muncul Reels baru, alurnya benar.
Kalau error, kirim pesan errornya, gampang di-debug dari log yang muncul.

### 6. Setup jadwal otomatis (cron)
```
sv-enable crond
sv up crond
crontab -e
```
Isi 2 baris ini (sesuaikan path kalau folder beda):
```
0 6 * * * cd /data/data/com.termux/files/home/ig-movie-bot && python main.py >> log.txt 2>&1
0 19 * * * cd /data/data/com.termux/files/home/ig-movie-bot && python main.py >> log.txt 2>&1
```
Simpan (`Ctrl+O` → `Enter` → `Ctrl+X`), lalu cek dengan `crontab -l`.

### 7. Biar tetap jalan walau HP idle
```
termux-wake-lock
```
Dan matikan battery optimization untuk Termux di Android Settings → Apps →
Termux → Battery → Unrestricted. Tanpa ini, Android bisa "membekukan" Termux
saat HP idle lama, jadi cron gak jalan tepat waktu.

## Catatan
- Font teks reveal judul di video "guess-the-movie": kalau mau custom, taruh
  file `.ttf` di folder `fonts/Poppins-Bold.ttf`. Kalau tidak ada, otomatis
  fallback ke font default sistem (DejaVu Sans Bold, biasanya sudah ada di
  Termux lewat paket `fontconfig` — install dengan `pkg install fontconfig`
  kalau font fallback belum ketemu).
- Video disimpan sementara di GitHub repo (folder `media/`) hanya selama
  proses publish, lalu otomatis dihapus lagi setelah berhasil post — supaya
  repo tidak numpuk file besar.
- Cek `log.txt` di folder project kalau mau lihat riwayat run cron.
