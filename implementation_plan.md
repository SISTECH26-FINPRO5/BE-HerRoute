# 🚀 Implementation Plan — BE FastAPI (ML-HerRoute)

Rencana ini disusun berurutan (Fase 0 → 7), tiap fase punya checklist yang bisa
dicentang langsung. Kerjain berurutan — jangan loncat ke fase endpoint sebelum
loader-nya beres, karena semua endpoint gantung ke artifacts yang di-load di Fase 2.

---

## Fase 0 — Persiapan Repo & Artifacts

- [x] Buat repo/folder project baru: `ml-herroute-be/`
- [x] Copy folder `export/` dari notebook ke `ml-herroute-be/artifacts/`
      (isinya: `champion_model.joblib`, `model_context.joblib`,
      `cell_hist_lookup.joblib`, `remap_bounds.joblib`, `risk_graph_source.joblib`,
      `safe_places.csv`, `model_config.csv`)
- [x] Jangan copy folder `models/` — itu cuma riwayat training, BE gak butuh
- [x] Init virtualenv, install dependency dasar:
  ```bash
  pip install fastapi uvicorn[standard] scikit-learn pandas numpy networkx joblib \
              supabase python-dotenv pydantic
  ```
- [x] Buat file `.env` (jangan commit), isi kredensial Supabase yang sudah ada:
  ```
  SUPABASE_URL=...
  SUPABASE_KEY=...
  ```
- [x] Struktur folder awal:
  ```text
  ml-herroute-be/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── config.py
  │   ├── db.py                 <- koneksi Supabase
  │   ├── ml/
  │   │   ├── __init__.py
  │   │   ├── loader.py          <- Fase 2
  │   │   ├── functions.py       <- Fase 3
  │   │   └── graph.py           <- Fase 3
  │   ├── schemas.py             <- Fase 4
  │   └── routers/
  │       ├── __init__.py
  │       ├── risk.py            <- Fase 5
  │       ├── safe_places.py     <- Fase 5
  │       ├── route.py           <- Fase 5
  │       └── reports.py         <- Fase 6
  ├── artifacts/                 <- dari Fase 0
  ├── .env
  ├── requirements.txt
  └── README.md
  ```

---

## Fase 1 — Konfigurasi Dasar

- [ ] `app/config.py` — baca `.env`, expose `SUPABASE_URL`, `SUPABASE_KEY`,
      path ke folder `artifacts/`
- [ ] `app/db.py` — bikin Supabase client:
  ```python
  from supabase import create_client
  from app.config import SUPABASE_URL, SUPABASE_KEY

  supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
  ```
- [ ] Di dashboard Supabase (bukan di kode), buat tabel `reports`:
  | Kolom | Tipe | Catatan |
  | :-- | :-- | :-- |
  | `id` | `uuid`, default `gen_random_uuid()` | primary key |
  | `lat` | `float8` | |
  | `lon` | `float8` | |
  | `category` | `text` | |
  | `description` | `text` | nullable |
  | `created_at` | `timestamptz`, default `now()` | |

  ⚠️ **Tidak ada** kolom identitas user (no `user_id`, `email`, `ip_address`, dst) —
  ini fitur anonymous reporting.
- [ ] Aktifkan Row Level Security (RLS) di tabel `reports`, buat policy: `insert`
      terbuka untuk semua (anon), `select` terbuka untuk semua (anon) — sesuaikan
      kalau nanti butuh moderasi.

---

## Fase 2 — ML Loader (Startup)

- [ ] `app/ml/loader.py` — class/fungsi yang load semua artifacts **sekali** saat
      startup:
  ```python
  import joblib
  import numpy as np
  import pandas as pd
  from pathlib import Path
  from sklearn.neighbors import BallTree
  from app.ml.graph import build_risk_graph

  EARTH_RADIUS_M = 6_371_000
  ARTIFACTS_DIR = Path("artifacts")

  class MLContext:
      def __init__(self):
          self.model = joblib.load(ARTIFACTS_DIR / "champion_model.joblib")

          ctx = joblib.load(ARTIFACTS_DIR / "model_context.joblib")
          self.cell_target_map = ctx["cell_target_map"]
          self.global_mean_val = ctx["global_mean_val"]
          self.T_LOW = ctx["T_LOW"]
          self.T_HIGH = ctx["T_HIGH"]
          self.GRID_DECIMALS = ctx["GRID_DECIMALS"]
          self.FEATURE_COLS_V2 = ctx["FEATURE_COLS_V2"]

          hist = joblib.load(ARTIFACTS_DIR / "cell_hist_lookup.joblib")
          self.cell_hist_lookup = hist["cell_hist_lookup"]
          self.cell_hist_tree = BallTree(
              np.radians(self.cell_hist_lookup[["lat_r", "lon_r"]].values),
              metric="haversine",
          )

          self.remap_bounds = joblib.load(ARTIFACTS_DIR / "remap_bounds.joblib")

          self.safe_places_df = pd.read_csv(ARTIFACTS_DIR / "safe_places.csv")
          self.safe_place_tree = BallTree(
              np.radians(self.safe_places_df[["lat", "lon"]].values),
              metric="haversine",
          )

          graph_src = joblib.load(ARTIFACTS_DIR / "risk_graph_source.joblib")
          self.risk_graph = build_risk_graph(graph_src["df_for_graph"])

  ml_context: MLContext | None = None

  def get_ml_context() -> MLContext:
      if ml_context is None:
          raise RuntimeError("MLContext belum di-load. Cek lifespan startup di main.py")
      return ml_context
  ```
- [ ] Test manual: jalanin `python -c "from app.ml.loader import MLContext; MLContext()"`,
      pastiin gak error dan `risk_graph` punya 1 komponen (cek log
      `nx.number_connected_components`).

---

## Fase 3 — Fungsi ML (copy dari notebook)

- [ ] `app/ml/functions.py` — isi: `remap_coord`, `snap_to_nearest_cell`,
      `assemble_features_v2_dynamic`, `get_risk_indicator`,
      `find_nearest_safe_places`, `find_nearest_safe_places_jkt`
      (copy persis dari prompt yang sudah dikasih ke AI BE sebelumnya, cuma
      parameternya ambil dari `MLContext`, bukan variabel global notebook)
- [ ] `app/ml/graph.py` — isi: `connect_components`, `build_risk_graph`, `find_route`
      (copy persis, ini yang dipanggil `loader.py` di Fase 2)
- [ ] Update `app/ml/loader.py`: ganti `ml_context = None` jadi di-assign lewat
      lifespan event di `main.py` (lihat Fase 7), bukan langsung di import time

---

## Fase 4 — Pydantic Schemas

- [ ] `app/schemas.py`:
  ```python
  from pydantic import BaseModel
  from typing import Literal, Optional
  from datetime import datetime

  class RiskIndicatorRequest(BaseModel):
      lat: float
      lon: float
      dow: int   # 0-6
      hour: int  # 0-23

  class RiskIndicatorResponse(BaseModel):
      cell_id: str
      risk_score: float
      tier: str
      color: str
      is_mock: bool
      mock_note: str

  class SafePlace(BaseModel):
      name: str
      amenity_type: str
      lat: float
      lon: float

  class SafePlacesResponse(BaseModel):
      places: list[SafePlace]
      is_mock: bool

  class SafeRouteRequest(BaseModel):
      start_lat: float
      start_lon: float
      end_lat: float
      end_lon: float
      mode: Literal["safe", "fast"] = "safe"

  class SafeRouteResponse(BaseModel):
      path: list[str]
      n_cells: int
      avg_risk: float
      mode: str
      is_mock: bool

  class ReportCreate(BaseModel):
      lat: float
      lon: float
      category: str
      description: Optional[str] = None

  class ReportResponse(BaseModel):
      id: str
      lat: float
      lon: float
      category: str
      description: Optional[str]
      created_at: datetime
  ```

---

## Fase 5 — Endpoint Prediksi (risk, safe-places, route)

- [ ] `app/routers/risk.py` — `POST /risk-indicator`, panggil `get_risk_indicator()`
      pakai `MLContext` dari dependency injection
- [ ] `app/routers/safe_places.py` — `GET /safe-places?lat=..&lon=..&k=5`, panggil
      `find_nearest_safe_places_jkt()`
- [ ] `app/routers/route.py` — `POST /safe-route`:
  1. `remap_coord()` kedua titik
  2. `snap_to_nearest_cell()` kedua titik → dapat `start_cell`, `end_cell`
  3. `find_route(ml_context.risk_graph, start_cell, end_cell, mode)`
  4. Kalau `path is None` → `raise HTTPException(404, detail="Rute tidak ditemukan antara dua titik ini")`
  5. Return `path`, `len(path)`, `avg_risk`, `mode`, `is_mock: True`
- [ ] Semua tiga router pakai dependency yang sama buat ambil `MLContext`:
  ```python
  from fastapi import Request

  def get_ctx(request: Request):
      return request.app.state.ml_context
  ```

---

## Fase 6 — Endpoint Reports (Supabase)

- [ ] `app/routers/reports.py`:
  ```python
  from fastapi import APIRouter, HTTPException
  from app.db import supabase
  from app.schemas import ReportCreate, ReportResponse

  router = APIRouter()

  @router.post("/reports", response_model=ReportResponse)
  def create_report(report: ReportCreate):
      result = supabase.table("reports").insert(report.model_dump()).execute()
      if not result.data:
          raise HTTPException(500, detail="Gagal menyimpan laporan")
      return result.data[0]

  @router.get("/reports", response_model=list[ReportResponse])
  def list_reports(limit: int = 50):
      result = (
          supabase.table("reports")
          .select("*")
          .order("created_at", desc=True)
          .limit(limit)
          .execute()
      )
      return result.data
  ```
- [ ] Pastikan `ReportCreate` **tidak** punya field identitas apapun sebelum
      di-insert (double-check di kode, jangan cuma andalkan schema tabel)

---

## Fase 7 — Wiring `main.py` (Lifespan + CORS)

- [ ] `app/main.py`:
  ```python
  from contextlib import asynccontextmanager
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  from app.ml.loader import MLContext
  from app.routers import risk, safe_places, route, reports

  @asynccontextmanager
  async def lifespan(app: FastAPI):
      app.state.ml_context = MLContext()  # load sekali saat startup
      yield
      # cleanup kalau perlu, biasanya gak ada untuk ini

  app = FastAPI(title="ML-HerRoute API", lifespan=lifespan)

  app.add_middleware(
      CORSMiddleware,
      allow_origins=["https://your-frontend-domain.com", "http://localhost:3000"],
      allow_methods=["*"],
      allow_headers=["*"],
  )

  app.include_router(risk.router, tags=["risk"])
  app.include_router(safe_places.router, tags=["safe-places"])
  app.include_router(route.router, tags=["route"])
  app.include_router(reports.router, tags=["reports"])
  ```
- [ ] Ganti `allow_origins` sesuai domain FE beneran (jangan `"*"` kalau nanti
      pakai cookies/auth apapun)
- [ ] Jalanin: `uvicorn app.main:app --reload`
- [ ] Cek `http://localhost:8000/docs` — pastikan 5 endpoint muncul (`/risk-indicator`,
      `/safe-places`, `/safe-route`, `POST /reports`, `GET /reports`)

---

## Fase 8 — Testing Manual (checklist cepat)

- [ ] `POST /risk-indicator` dengan koordinat Bundaran HI → dapat `tier`, `color`,
      `is_mock: true`
- [ ] `GET /safe-places?lat=-6.244&lon=106.7996&k=5` → dapat 5 tempat aman
- [ ] `POST /safe-route` Blok M → Bundaran HI, mode `safe` → dapat `path` gak kosong
- [ ] Sama, mode `fast` → bandingkan `avg_risk`-nya (harusnya safe ≤ fast)
- [ ] `POST /reports` → cek muncul di tabel Supabase, tanpa kolom identitas
- [ ] `GET /reports` → dapat list, terurut terbaru dulu
- [ ] Uji endpoint dari FE (cek CORS gak nge-block)

---

## Fase 9 — Sebelum Deploy (nice-to-have, kalau waktu masih ada)

- [ ] Tambah `requirements.txt` (`pip freeze > requirements.txt`)
- [ ] Tambah `.gitignore` (`.env`, `__pycache__/`, `artifacts/` kalau ukurannya besar
      dan mau ditarik lewat script terpisah saat deploy)
- [ ] Rate limiting sederhana di `/reports` (biar gak di-spam)
- [ ] Logging dasar (siapa manggil endpoint apa, kapan) — bukan buat identitas user,
      cuma buat debugging traffic