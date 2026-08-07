from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ..database import supabase
import pandas as pd
import json

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])

@router.get("/logs", response_model=List[Dict[str, Any]])
def get_prediction_logs(limit: int = 50):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")

    try:
        response = supabase.table("prediction_logs").select("*").order("created_at", desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return []

@router.get("/metrics")
def get_prediction_metrics():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")

    try:
        response = supabase.table("prediction_logs").select("endpoint, latency_ms, prediction_result").execute()
        data = response.data
        
        total_predictions = len(data)
        if total_predictions == 0:
            return {"total_predictions": 0, "avg_latency_ms": 0, "endpoint_counts": {}, "risk_tier_counts": {}}
            
        avg_latency = sum(item.get("latency_ms", 0) for item in data) / total_predictions
        
        endpoint_counts = {}
        risk_tier_counts = {"Aman": 0, "Waspada": 0, "Rawan": 0}
        
        for item in data:
            ep = item.get("endpoint", "unknown")
            endpoint_counts[ep] = endpoint_counts.get(ep, 0) + 1
            
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
        return {"total_predictions": 0, "avg_latency_ms": 0, "endpoint_counts": {}, "risk_tier_counts": {}}

@router.get("/evaluations")
def get_model_evaluations():
    """
    Get historical model evaluation metrics for the dashboard from models_artifacts/registry_v2.csv.
    """
    try:
        df = pd.read_csv("models_artifacts/registry_v2.csv")
        df = df.dropna(subset=['metrics.MAE', 'metrics.RMSE', 'metrics.R2'])
        
        evaluations = []
        for _, row in df.iterrows():
            version_name = f"v{int(row['version'])} ({row['strategy']})"
            evaluations.append({
                "version": version_name,
                "mae": round(float(row['metrics.MAE']), 4),
                "rmse": round(float(row['metrics.RMSE']), 4),
                "r2_score": round(float(row['metrics.R2']), 4),
                "created_at": str(row['timestamp'])
            })
        return evaluations
    except Exception as e:
        print(f"Error reading evaluations from registry_v2.csv: {e}")
        return []
