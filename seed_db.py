import os
import random
import uuid
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL", "")
key = os.getenv("SUPABASE_KEY", "")

from supabase import create_client, Client
supabase: Client = create_client(url, key)

print("Starting to seed database...")

print("1. Seeding prediction_logs...")
endpoints = ["/risk-indicator", "/safe-route", "/safe-places"]
for _ in range(55):
    ep = random.choice(endpoints)
    lat = -6.2 + random.uniform(-0.1, 0.1)
    lon = 106.8 + random.uniform(-0.1, 0.1)
    latency = random.uniform(10.0, 150.0)
    tier = random.choice(["Aman", "Aman", "Waspada", "Rawan"])
    
    input_data = {"lat": lat, "lon": lon}
    result_data = {"tier": tier, "risk_score": random.uniform(0, 100)}
    
    log_entry = {
        "endpoint": ep,
        "latency_ms": latency,
        "input_data": input_data,
        "prediction_result": result_data,
        "model_version": "1.0",
        "created_at": (datetime.utcnow() - timedelta(minutes=random.randint(1, 10000))).isoformat()
    }
    
    try:
        supabase.table("prediction_logs").insert(log_entry).execute()
    except Exception as e:
        print(f"Failed to insert log: {e}")

print("2. Seeding reports...")
categories = ["Pelecehan Seksual", "Pencurian", "Jalanan Gelap", "Orang Mencurigakan"]
for _ in range(55):
    report_entry = {
        "lat": -6.2 + random.uniform(-0.1, 0.1),
        "lon": 106.8 + random.uniform(-0.1, 0.1),
        "category": random.choice(categories),
        "description": "Laporan dummy dari sistem seeding.",
        "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat()
    }
    try:
        supabase.table("reports").insert(report_entry).execute()
    except Exception as e:
        print(f"Failed to insert report: {e}")

print("3. Seeding users and trusted contacts...")
user_ids = []
for i in range(25):
    email = f"dummy_{uuid.uuid4().hex[:8]}@example.com"
    password = "Password123!"
    try:
        res = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"full_name": f"Dummy User {i}"}}
        })
        if res.user:
            user_ids.append(res.user.id)
    except Exception as e:
        print(f"Failed to create user: {e}")

print(f"Successfully created {len(user_ids)} users.")

if user_ids:
    contact_names = ["Mom", "Dad", "Brother", "Sister", "Bestie", "Boyfriend", "Husband", "Office"]
    contacts_created = 0
    while contacts_created < 55:
        for uid in user_ids:
            if contacts_created >= 55:
                break
            num_contacts = random.randint(1, 3)
            for _ in range(num_contacts):
                if contacts_created >= 55:
                    break
                c_entry = {
                    "user_id": uid,
                    "name": random.choice(contact_names),
                    "phone_number": f"+628{random.randint(10000000, 99999999)}"
                }
                try:
                    supabase.table("trusted_contacts").insert(c_entry).execute()
                    contacts_created += 1
                except Exception as e:
                    print(f"Failed to insert trusted contact: {e}")
                    break

print(f"Successfully seeded {contacts_created} trusted contacts.")
print("Seeding finished!")
