import json
from datetime import datetime
from .database import supabase

def log_prediction(endpoint: str, latency_ms: float, input_data: dict, prediction_result: dict, model_version: str = "1.0"):
    """
    Log prediction activity to Supabase asynchronously.
    """
    if not supabase:
        print(f"Warning: Supabase not initialized, skipped logging for {endpoint}")
        return

    try:
        log_entry = {
            "endpoint": endpoint,
            "latency_ms": latency_ms,
            "input_data": json.dumps(input_data),
            "prediction_result": json.dumps(prediction_result),
            "model_version": model_version,
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("prediction_logs").insert(log_entry).execute()
        if not response.data:
            print(f"Warning: Failed to log prediction for {endpoint}")
    except Exception as e:
        print(f"Error logging prediction: {e}")
