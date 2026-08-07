<h1 align="center">
  BE-HerRoute
</h1>

<p align="center">
  <strong>Backend untuk Navigasi Rute Aman & Indikator Keselamatan Perempuan</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase" />
  <img src="https://img.shields.io/badge/scikit_learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="scikit-learn" />
</p>

---

## 📖 Gambaran Umum

**HerRoute** adalah aplikasi pencari rute aman berbasis *machine learning* yang dirancang khusus untuk membantu perempuan bernavigasi di jalanan kota dengan aman, baik siang maupun malam hari. Repositori ini berisi sistem **Backend (BE)**, yang dibangun untuk beroperasi sangat cepat, tangguh, dan terintegrasi secara mendalam dengan algoritma *Machine Learning* tingkat lanjut untuk graf jalanan dan pencarian spasial.

## 🛠 Teknologi yang Digunakan

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Framework Python asinkron dengan performa tinggi)
- **Database & Auth**: [Supabase](https://supabase.com/) (PostgreSQL & Row-Level Security)
- **Machine Learning**: 
  - `scikit-learn` (GradientBoostingRegressor & BallTree untuk *query* spasial)
  - `networkx` (Pembuatan Graf dan optimasi rute A*)
  - `pandas` & `numpy` (Komputasi matriks/array berkecepatan tinggi)

## 🏁 Panduan Instalasi

### 1. Prasyarat (Prerequisites)
- Python 3.8+
- Git

### 2. Instalasi
```bash
# Clone repositori
git clone https://github.com/SISTECH26-FINPRO5/BE-HerRoute.git
cd BE-HerRoute

# Buat virtual environment
python -m venv venv
source venv/bin/activate  # Untuk Windows: venv\Scripts\activate

# Install dependensi (library)
pip install -r requirements.txt
```

### 3. Konfigurasi Environment Variables
Buat file `.env` di dalam root direktori berdasarkan *template* `.env.example`:
```bash
cp .env.example .env
```
Isi variabel di dalamnya dengan kredensial Supabase kamu:
- `SUPABASE_URL`: URL proyek Supabase milikmu.
- `SUPABASE_KEY`: Kunci anonim (anon key) dari proyek Supabase milikmu.
- `FRONTEND_URL`: URL untuk aplikasi *frontend* (default: `http://localhost:3000`).

### 4. Menjalankan Aplikasi
```bash
uvicorn app.main:app --reload
```
Aplikasi akan langsung berjalan di `http://localhost:8000`. 
Kamu bisa membuka dokumentasi API interaktif (Swagger) di: **`http://localhost:8000/docs`**

## 🌐 Daftar Endpoint API

### Autentikasi & Pengguna (Auth)
- `POST /register` : Mendaftarkan akun pengguna baru
- `POST /login` : Autentikasi pengguna dan mendapatkan sesi (session)
- `GET /auth/google` : Login menggunakan Google OAuth
- `POST /logout` : Mengakhiri sesi pengguna

### Kontak Darurat (Trusted Contacts)
- `GET /trusted-contacts` : Mengambil semua data kontak darurat milik pengguna
- `POST /trusted-contacts` : Menambahkan kontak darurat baru
- `DELETE /trusted-contacts/{id}` : Menghapus sebuah kontak darurat

### Machine Learning & Pencarian Rute
- `POST /api/ml/risk-indicator` : Memprediksi risiko keamanan di suatu koordinat pada jam/hari tertentu.
- `GET /api/ml/safe-places` : Mencari tempat aman terdekat (minimarket, pos polisi) menggunakan pencarian spasial `BallTree`.
- `POST /api/ml/safe-route` : Menghasilkan rute terbaik dari Titik A ke Titik B dengan prioritas optimasi (`fast` / cepat atau `safe` / aman).
- `GET /api/ml/reports` : Mengambil semua data laporan kejahatan/pelecehan publik yang di-submit secara anonim.
- `POST /api/ml/reports` : Menambahkan laporan kejahatan anonim yang dipetakan langsung ke fitur geospasial.

## Sorotan Arsitektur (Architecture Highlights)
- **Pre-computed Risk Graph**: Untuk menghindari waktu *startup* yang lambat, graf jalanan kota yang masif (lebih dari 12.000 koneksi) sudah di-*compile* sebelumnya dan diekspor sebagai `.joblib`. Ini memungkinkan backend untuk menyala dalam waktu kurang dari satu detik (*sub-second boot time*).
- **BallTree Spatial Indexing**: Menggunakan `sklearn.neighbors.BallTree` dengan metrik jarak *haversine* untuk pencarian tetangga terdekat dengan kecepatan kilat `$O(N \log N)$` pada bidang bola (Bumi).

