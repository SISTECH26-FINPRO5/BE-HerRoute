from fastapi import APIRouter, Request, HTTPException, status
from typing import List, Optional
import numpy as np
import pandas as pd
import networkx as nx
from ..schemas import (
    RiskIndicatorRequest, RiskIndicatorResponse,
    SafePlaceResponse, SafeRouteRequest, SafeRouteResponse,
    ReportCreate, ReportResponse
)
from ..database import supabase

router = APIRouter(prefix="/api/ml", tags=["ML endpoints"])

def remap_coord(lat, lon, JKT_LAT_RANGE, JKT_LON_RANGE, CHI_LAT_RANGE, CHI_LON_RANGE):
    lat_frac = (lat - JKT_LAT_RANGE[0]) / (JKT_LAT_RANGE[1] - JKT_LAT_RANGE[0])
    lon_frac = (lon - JKT_LON_RANGE[0]) / (JKT_LON_RANGE[1] - JKT_LON_RANGE[0])
    mock_lat = CHI_LAT_RANGE[0] + lat_frac * (CHI_LAT_RANGE[1] - CHI_LAT_RANGE[0])
    mock_lon = CHI_LON_RANGE[0] + lon_frac * (CHI_LON_RANGE[1] - CHI_LON_RANGE[0])
    return mock_lat, mock_lon

def snap_to_nearest_cell(lat, lon, cell_hist_tree, cell_hist_lookup):
    query = np.radians([[lat, lon]])
    _, idx = cell_hist_tree.query(query, k=1)
    
    if isinstance(cell_hist_lookup, pd.DataFrame):
        nearest = cell_hist_lookup.iloc[idx[0][0]]
    else:
        df = pd.DataFrame(cell_hist_lookup)
        nearest = df.iloc[idx[0][0]]
        
    return nearest["cell_id"], nearest["hist_crime_count"], nearest["crime_diversity"]

def assemble_features_v2_dynamic(data, cell_target_map, global_mean_val, feature_cols):
    data = data.copy()
    data["cell_target_enc"] = data["cell_id"].map(cell_target_map).fillna(global_mean_val)
    for col in feature_cols:
        if col not in data.columns:
            data[col] = 0
    return data[feature_cols]

@router.post("/risk-indicator", response_model=RiskIndicatorResponse)
def get_risk_indicator(request: Request, body: RiskIndicatorRequest):
    artifacts = request.app.state.ml_artifacts
    model = artifacts["champion_model"]
    model_context = artifacts["model_context"]
    cell_hist_tree = artifacts["cell_hist_tree"]
    cell_hist_lookup = artifacts["cell_hist_lookup"]
    remap_bounds = artifacts["remap_bounds"]
    
    cell_target_map = model_context["cell_target_map"]
    global_mean_val = model_context["global_mean_val"]
    T_LOW = model_context["T_LOW"]
    T_HIGH = model_context["T_HIGH"]
    GRID_DECIMALS = model_context["GRID_DECIMALS"]
    FEATURE_COLS_V2 = model_context["FEATURE_COLS_V2"]
    
    mock_lat, mock_lon = remap_coord(body.lat, body.lon, **remap_bounds)
    lat_r = round(mock_lat, GRID_DECIMALS)
    lon_r = round(mock_lon, GRID_DECIMALS)
    cell_id = f"{lat_r}_{lon_r}"
    
    snapped_cell_id, hist_crime_count, crime_diversity = snap_to_nearest_cell(
        lat_r, lon_r, cell_hist_tree, cell_hist_lookup)
        
    row = pd.DataFrame([{
        "cell_id": snapped_cell_id, "lat_r": lat_r, "lon_r": lon_r,
        "dow": body.dow, "hour": body.hour,
        "hour_sin": np.sin(2 * np.pi * body.hour / 24), "hour_cos": np.cos(2 * np.pi * body.hour / 24),
        "dow_sin": np.sin(2 * np.pi * body.dow / 7), "dow_cos": np.cos(2 * np.pi * body.dow / 7),
        "hist_crime_count": hist_crime_count, "crime_diversity": crime_diversity,
    }])
    X = assemble_features_v2_dynamic(row, cell_target_map, global_mean_val, FEATURE_COLS_V2)
    risk_score = float(np.clip(model.predict(X)[0], 0, 100))
    
    if risk_score >= T_HIGH:
        tier, color = "Rawan", "red"
    elif risk_score >= T_LOW:
        tier, color = "Waspada", "yellow"
    else:
        tier, color = "Aman", "green"
        
    return {
        "cell_id": cell_id, "risk_score": round(risk_score, 2), "tier": tier, "color": color,
        "is_mock": True,
        "mock_note": "Skor ini hasil simulasi, koordinat Jakarta ditempelkan ke sel Chicago asli terdekat untuk mengambil pola historisnya, bukan cerminan kondisi keamanan Jakarta yang sesungguhnya."
    }

@router.get("/safe-places", response_model=List[SafePlaceResponse])
def get_safe_places(request: Request, lat: float, lon: float, k: int = 5):
    artifacts = request.app.state.ml_artifacts
    safe_place_tree = artifacts["safe_place_tree"]
    safe_places_df = artifacts["safe_places_df"]
    remap_bounds = artifacts["remap_bounds"]
    EARTH_RADIUS_M = artifacts["EARTH_RADIUS_M"]
    
    mock_lat, mock_lon = remap_coord(lat, lon, **remap_bounds)
    
    query = np.radians([[mock_lat, mock_lon]])
    dist_rad, idx = safe_place_tree.query(query, k=k)
    dist_m = dist_rad[0] * EARTH_RADIUS_M
    
    result = safe_places_df.iloc[idx[0]].copy()
    result["is_mock"] = True
    
    places = []
    for _, row in result.iterrows():
        places.append({
            "name": row["name"],
            "amenity_type": row["amenity_type"],
            "lat": row["lat"],
            "lon": row["lon"],
            "is_mock": True
        })
    return places

@router.post("/safe-route", response_model=SafeRouteResponse)
def get_safe_route(request: Request, body: SafeRouteRequest):
    artifacts = request.app.state.ml_artifacts
    cell_hist_tree = artifacts["cell_hist_tree"]
    cell_hist_lookup = artifacts["cell_hist_lookup"]
    remap_bounds = artifacts["remap_bounds"]
    model_context = artifacts["model_context"]
    GRID_DECIMALS = model_context["GRID_DECIMALS"]
    G = artifacts["risk_graph"]
    
    s_mock_lat, s_mock_lon = remap_coord(body.start_lat, body.start_lon, **remap_bounds)
    s_lat_r = round(s_mock_lat, GRID_DECIMALS)
    s_lon_r = round(s_mock_lon, GRID_DECIMALS)
    start_cell, _, _ = snap_to_nearest_cell(s_lat_r, s_lon_r, cell_hist_tree, cell_hist_lookup)
    
    e_mock_lat, e_mock_lon = remap_coord(body.end_lat, body.end_lon, **remap_bounds)
    e_lat_r = round(e_mock_lat, GRID_DECIMALS)
    e_lon_r = round(e_mock_lon, GRID_DECIMALS)
    end_cell, _, _ = snap_to_nearest_cell(e_lat_r, e_lon_r, cell_hist_tree, cell_hist_lookup)
    
    weight_key = "weight_safe" if body.mode == "safe" else "weight_fast"
    
    if start_cell not in G or end_cell not in G:
        raise HTTPException(status_code=404, detail="Start or end cell not found in risk graph.")
        
    try:
        path = nx.shortest_path(G, start_cell, end_cell, weight=weight_key)
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail="Tidak ada rute yang tersedia di antara kedua titik tersebut.")
        
    avg_risk_path = np.mean([G.nodes[c].get("risk", 0) for c in path])
    
    return {
        "path": path,
        "avg_risk": round(avg_risk_path, 2),
        "is_mock": True,
        "mock_note": "Rute ini hasil simulasi pada graf Chicago, bukan jalan Jakarta yang sesungguhnya."
    }

@router.post("/reports", response_model=ReportResponse)
def create_report(body: ReportCreate):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
        
    try:
        data = {
            "lat": body.lat,
            "lon": body.lon,
            "category": body.category,
            "description": body.description
        }
        response = supabase.table("reports").insert(data).execute()
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create report")
            
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/reports", response_model=List[ReportResponse])
def get_reports():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
        
    try:
        response = supabase.table("reports").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
