# BE-HerRoute

This is the backend for the HerRoute application, built with FastAPI and Supabase.

## Requirements
- Python 3.8+
- [FastAPI](https://fastapi.tiangolo.com/)
- [Supabase](https://supabase.com/)

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/SISTECH26-FINPRO5/BE-HerRoute.git
cd BE-HerRoute
```

### 2. Set up a virtual environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Variables
Create a `.env` file in the root directory based on the `.env.example` provided:
```bash
cp .env.example .env
```
Fill in the variables in `.env` with your Supabase credentials:
- `SUPABASE_URL`: Your Supabase project URL.
- `SUPABASE_KEY`: Your Supabase project anon key.
- `FRONTEND_URL`: URL of the frontend app (default: http://localhost:3000).

### 5. Run the application
To start the server, run:
```bash
uvicorn app.main:app --reload
```

The application will be available at `http://localhost:8000`. You can access the interactive API documentation at `http://localhost:8000/docs`.

## API Progress

Here is the list of APIs that have been implemented so far:

- `GET /`            : Root endpoint (Health check)
- `POST /register`   : User registration
- `POST /login`      : User login
- `GET /auth/google` : Google OAuth authentication
- `POST /logout`     : User logout
