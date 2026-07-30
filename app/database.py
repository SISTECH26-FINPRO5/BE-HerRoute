import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.getenv("SUPABASE_URL", "")
key: str = os.getenv("SUPABASE_KEY", "")
frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

supabase: Client = None
if url and key and url != "your-supabase-url-here" and key != "your-supabase-anon-key-here":
    supabase = create_client(url, key)
