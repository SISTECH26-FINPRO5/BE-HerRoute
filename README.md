<h1 align="center">
  BE-HerRoute
</h1>

<p align="center">
  <strong>A Backend for Safe Routing & Safety Indicator for Women</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase" />
  <img src="https://img.shields.io/badge/scikit_learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="scikit-learn" />
</p>

---

## 📖 Overview

**HerRoute** is a machine learning-powered safety routing application specifically designed to help women navigate city streets safely, day or night. This repository contains the **Backend**, built to be incredibly fast, robust, and heavily integrated with advanced Machine Learning graph-routing and spatial search algorithms.

## 🛠 Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (High performance, async python framework)
- **Database & Auth**: [Supabase](https://supabase.com/) (PostgreSQL & Row-Level Security)
- **Machine Learning**: 
  - `scikit-learn` (GradientBoostingRegressor & BallTree for spatial queries)
  - `networkx` (Graph creation and A* routing optimization)
  - `pandas` & `numpy` (Fast matrix/array computations)

## 🏁 Getting Started

### 1. Prerequisites
- Python 3.8+
- Git

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/SISTECH26-FINPRO5/BE-HerRoute.git
cd BE-HerRoute

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory based on `.env.example`:
```bash
cp .env.example .env
```
Fill in your Supabase credentials:
- `SUPABASE_URL`: Your Supabase project URL.
- `SUPABASE_KEY`: Your Supabase project anon key.
- `FRONTEND_URL`: URL of the frontend app (default: `http://localhost:3000`).

### 4. Running the Application
```bash
uvicorn app.main:app --reload
```
The application will instantly start at `http://localhost:8000`. 
Check out the interactive Swagger API documentation at: **`http://localhost:8000/docs`**

## 🌐 API Endpoints

### Auth & Users
- `POST /register` : Create a new user account
- `POST /login` : Authenticate user and get session
- `GET /auth/google` : Google OAuth login
- `POST /logout` : End user session

### Trusted Contacts
- `GET /trusted-contacts` : Get all trusted emergency contacts
- `POST /trusted-contacts` : Add a new trusted contact
- `DELETE /trusted-contacts/{id}` : Remove a trusted contact

### Machine Learning & Routing
- `POST /api/ml/risk-indicator` : Predicts safety risk at a coordinate for a specific time/day.
- `GET /api/ml/safe-places` : Finds nearest safe places (minimarkets, police stations) via `BallTree` spatial search.
- `POST /api/ml/safe-route` : Generates the best route from Point A to Point B with optimization priorities (`fast` or `safe`).
- `GET /api/ml/reports` : Retrieve all submitted anonymous crime/harassment reports.
- `POST /api/ml/reports` : Anonymous submission of crime/harassment reports directly mapped to geospatial features.

## Architecture Highlights
- **Pre-computed Risk Graph**: To avoid slow startup times, the massive 12,000+ edges city street graph is pre-compiled and exported as `.joblib`, allowing the backend to achieve a sub-second boot time.
- **BallTree Spatial Indexing**: We utilize `sklearn.neighbors.BallTree` with haversine distance for blazing fast `$O(N \log N)$` nearest-neighbor lookups on a sphere (Earth).

