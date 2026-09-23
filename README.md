# 🔍 Google Maps Playwright Scraper

Scraping data bisnis dari Google Maps **tanpa API key** menggunakan Playwright (browser automation).

## ✨ Fitur

- **Gratis** — tidak perlu API key
- **Data lengkap** — nama, alamat, telepon, email, rating, review, kategori, jam operasional, website
- **Stealth mode** — bypass anti-bot detection
- **Auto scroll** — otomatis scroll untuk load semua hasil
- **Random delay** — delay acak 2-4 detik agar terlihat natural
- **Debug mode** — `--visible` flag untuk melihat browser berjalan

## 📦 Install

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Chromium browser untuk Playwright
playwright install chromium
```

## 🚀 Penggunaan

```bash
# Contoh dasar
python gmaps_playwright_scraper.py --type "angkringan" --area "purwokerto"

# Dengan browser terlihat (untuk debug/monitoring)
python gmaps_playwright_scraper.py --type "warung makan" --area "semarang" --visible

# Custom folder output
python gmaps_playwright_scraper.py --type "toko baju" --area "yogyakarta" --output-dir "./hasil"
```

## 📊 Output CSV

File CSV akan berisi kolom-kolom berikut:

| Kolom | Deskripsi |
|-------|-----------|
| `nama` | Nama tempat/bisnis |
| `alamat` | Alamat lengkap |
| `nomor_hp` | Nomor telepon |
| `email` | Email (jarang ada di Google Maps) |
| `rating` | Rating (1-5) |
| `total_review` | Jumlah review |
| `kategori` | Kategori bisnis |
| `website` | URL website (jika ada) |
| `jam_operasional` | Jam buka/tutup |
| `google_maps_url` | Link ke Google Maps |
| `place_id` | Identifier tempat |

## ⚠️ Catatan Penting

- **Jangan jalankan terlalu sering** — bisa kena block oleh Google
- **Gunakan `--visible`** jika sering gagal, untuk melihat apakah ada CAPTCHA
- **Selector bisa berubah** — jika Google mengubah struktur HTML-nya, script mungkin perlu diupdate
- **Email jarang tersedia** — Google Maps memang jarang menampilkan email bisnis

## 🔧 Troubleshooting

| Masalah | Solusi |
|---------|--------|
| CAPTCHA muncul | Tunggu beberapa menit, jalankan ulang dengan `--visible` |
| Tidak ada hasil | Coba ubah query, misal "kedai kopi" bukan "coffee shop" |
| Timeout error | Pastikan koneksi internet stabil |
| Encoding error | Script sudah otomatis fix encoding untuk Windows |
