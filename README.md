# IG Movie Bot (trivia & guess-the-movie)

Bot posting otomatis ke Instagram Reels, 2x sehari (06:00 & 19:00 WIB), rotasi
random antara 2 tipe konten:
- **Trivia card** — fakta film dari TMDB (budget, cast, rating, dll)
- **Guess-the-movie** — backdrop di-blur bertahap, reveal judul di akhir

Sumber gambar: backdrop/still resmi dari TMDB (bukan capture video/trailer),
diolah jadi slideshow video dengan efek Ken Burns via ffmpeg. Tidak ada
konten video asli film yang di-download atau direpost.

## Setup

### 1. TMDB API Key
1. Daftar di https://www.themoviedb.org/ → Settings → API → minta API key (gratis).
2. Simpan sebagai `TMDB_API_KEY`.

### 2. Instagram Graph API
1. Akun Instagram harus **Business/Creator** dan terhubung ke Facebook Page.
2. Buat app di https://developers.facebook.com/ → tambahkan produk **Instagram Graph API**.
3. Minta izin `instagram_content_publish` dan `pages_show_list`.
4. Ambil `IG_USER_ID` (Instagram Business Account ID) lewat Graph API Explorer:
   `GET /me/accounts` → cari Page kamu → `GET /{page-id}?fields=instagram_business_account`
5. Generate long-lived access token, simpan sebagai `IG_ACCESS_TOKEN`.

### 3. Deploy ke Railway
1. Push folder ini ke repo GitHub kamu.
2. Di Railway: New Project → Deploy from GitHub repo.
3. Railway otomatis pakai `nixpacks.toml` (install ffmpeg + python).
4. Isi Environment Variables di Railway sesuai `.env.example`.
5. Setelah deploy pertama, copy URL publik Railway (mis. `https://xxx.up.railway.app`)
   dan isi ke variable `APP_PUBLIC_URL`, lalu redeploy.

### 4. Test manual sebelum jadwal otomatis jalan
```
curl -X POST https://<url-railway-kamu>/test-post
```
Cek Instagram — kalau muncul Reels baru, berarti alur sudah benar.

## Catatan
- Font untuk teks reveal judul di video "guess-the-movie": kalau mau custom,
  taruh file `.ttf` di folder `fonts/Poppins-Bold.ttf`. Kalau tidak ada,
  otomatis fallback ke font default sistem.
- Jadwal & timezone diatur di `main.py` (`Asia/Jakarta`), gampang diubah
  kalau mau tambah slot atau ganti jam.
- Video generate sementara disimpan di folder `media/` dan di-serve publik
  lewat `/media/<filename>` — ini dibutuhkan Instagram Graph API karena
  publishing butuh `video_url` yang bisa diakses dari luar.
