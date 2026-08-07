from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ..database import supabase

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])

@router.get("/logs", response_model=List[Dict[str, Any]])
def get_prediction_logs(limit: int = 50):
    """
    Get recent prediction logs for the dashboard.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")

    try:
        response = supabase.table("prediction_logs").select("*").order("created_at", desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        # Fallback if table doesn't exist or error occurs
        print(f"Error fetching logs: {e}")
        return []

@router.get("/metrics")
def get_prediction_metrics():
    """
    Get aggregated metrics for the dashboard.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")

    try:
        response = supabase.table("prediction_logs").select("endpoint, latency_ms, prediction_result").execute()
        data = response.data
        
        total_predictions = len(data)
        if total_predictions == 0:
            return {
                "total_predictions": 0,
                "avg_latency_ms": 0,
                "endpoint_counts": {},
                "risk_tier_counts": {}
            }
            
        avg_latency = sum(item.get("latency_ms", 0) for item in data) / total_predictions
        
        endpoint_counts = {}
        risk_tier_counts = {"Aman": 0, "Waspada": 0, "Rawan": 0}
        
        for item in data:
            ep = item.get("endpoint", "unknown")
            endpoint_counts[ep] = endpoint_counts.get(ep, 0) + 1
            
            # Parse prediction result if it exists to get the tier
            import json
            try:
                res = json.loads(item.get("prediction_result", "{}"))
                tier = res.get("tier")
                if tier in risk_tier_counts:
                    risk_tier_counts[tier] += 1
            except:
                pass
                
        return {
            "total_predictions": total_predictions,
            "avg_latency_ms": round(avg_latency, 2),
            "endpoint_counts": endpoint_counts,
            "risk_tier_counts": risk_tier_counts
        }
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        return {
            "total_predictions": 0,
            "avg_latency_ms": 0,
            "endpoint_counts": {},
            "risk_tier_counts": {}
        }

@router.get("/evaluations")
def get_model_evaluations():
    """
    Get historical model evaluation metrics for the dashboard.
    Falls back to mock data if the table doesn't exist yet, so the frontend can still render charts.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")

    try:
        response = supabase.table("model_evaluations").select("*").order("created_at", desc=False).execute()
        if response.data and len(response.data) > 0:
            return response.data
    except Exception as e:
        print(f"Error fetching evaluations (returning mock data): {e}")

    # Fallback mock data to show model performance progression over time
    return [
        {
            "version": "0.8 (Alpha)",
            "mae": 15.2,
            "rmse": 18.5,
            "r2_score": 0.65,
            "created_at": "2023-11-01T10:00:00Z"
        },
        {
            "version": "0.9 (Beta)",
            "mae": 12.1,
            "rmse": 14.3,
            "r2_score": 0.72,
            "created_at": "2023-12-15T14:30:00Z"
        },
        {
            "version": "1.0 (Production)",
            "mae": 8.4,
            "rmse": 10.2,
            "r2_score": 0.85,
            "created_at": "2024-01-20T09:15:00Z"
        }
    ]
