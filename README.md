# Google Maps Scraper

Script Python sederhana untuk mengumpulkan data tempat atau bisnis dari Google Maps secara otomatis dan menyimpannya langsung ke dalam file Excel/CSV.

Cocok untuk riset pasar atau mengumpulkan kontak bisnis (seperti nama tempat, alamat, nomor telepon, rating, dan website) tanpa harus menyalin satu per satu secara manual.

---

## Data yang Didapatkan

File hasil (.csv) yang disimpan akan berisi kolom:
- Nama tempat
- Rating (bintang)
- Perkiraan harga
- Kategori usaha
- Alamat lengkap
- Nomor telepon
- Email (jika tercantum)
- Website (jika ada)
- Link Google Maps

---

## Langkah Instalasi

Pastikan komputer sudah terinstall **Python** (versi 3.8 ke atas).

1. **Buka Terminal / Command Prompt** di folder project ini.

2. **Install library yang dibutuhkan:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install browser Chromium untuk Playwright:**
   ```bash
   playwright install chromium
   ```
   *(Langkah ini hanya perlu dilakukan satu kali di awal)*

---

## Cara Menjalankan

Jalankan perintah berikut di terminal:

```bash
python main.py --type "jenis usaha" --area "kota/daerah"
```

### Contoh Penggunaan

- **Mencari cafe di Purwokerto:**
  ```bash
  python main.py --type "cafe" --area "purwokerto"
  ```

- **Mencari toko baju di Semarang sambil memantau browsernya:**
  ```bash
  python main.py --type "toko baju" --area "semarang" --visible
  ```

- **Menyimpan hasil ke folder tertentu:**
  ```bash
  python main.py --type "klinik gigi" --area "surabaya" --output-dir "./hasil"
  ```

---

## Penjelasan Perintah

| Parameter | Keterangan |
|---|---|
| `--type` | *(Wajib)* Jenis usaha atau tempat yang ingin dicari (contoh: `"cafe"`, `"laundry"`, `"hotel"`). |
| `--area` | *(Wajib)* Nama wilayah, kota, atau daerah pencarian (contoh: `"purwokerto"`, `"jakarta selatan"`). |
| `--visible` | *(Opsional)* Jika ditambahkan, jendela browser akan tampil di layar saat proses scraping berjalan. Jika tidak dipakai, proses berjalan di latar belakang (tanpa membuka jendela baru). |
| `--output-dir` | *(Opsional)* Folder tempat menyimpan file hasil. Jika tidak diisi, otomatis tersimpan di folder `data`. |

---

## Cara Melihat Hasil

1. Setelah proses selesai, file CSV akan otomatis tersimpan di folder `data/` (atau folder yang Anda tentukan).
2. Nama file berformat: `[jenis_usaha]_[daerah]_[tanggal_jam].csv`.
3. File tersebut bisa langsung dibuka menggunakan **Microsoft Excel**, **Google Sheets**, atau text editor biasa.

---

## Catatan Penggunaan

- Setiap 20 data berhasil diambil, program akan berhenti sejenak dan menanyakan apakah Anda ingin lanjut ke 20 data berikutnya atau menyudahi dan langsung menyimpan hasil.
- Hindari menjalankan scraping terlalu intensif dalam waktu singkat agar terhindar dari pembatasan akses oleh Google.
- Jika pencarian tampak tidak menemukan hasil, coba jalankan dengan menambahkan `--visible` untuk melihat apakah ada kendala tampilan atau perlunya penyesuaian kata kunci pencarian.
