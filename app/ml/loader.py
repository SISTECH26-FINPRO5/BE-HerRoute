import os
import joblib
import pandas as pd
import numpy as np
import networkx as nx
from sklearn.neighbors import BallTree
import logging

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "artifacts")

def connect_components(G, cell_risk, EARTH_RADIUS_M, risk_weight=2.0):
    components = list(nx.connected_components(G))
    if len(components) <= 1:
        return G

    # Sort components by size (descending)
    components.sort(key=len, reverse=True)
    
    main_component = list(components[0])
    main_coords = np.radians([[float(node.split('_')[0]), float(node.split('_')[1])] for node in main_component])
    
    # Build tree for main component ONCE
    tree = BallTree(main_coords, metric='haversine')
    
    for i in range(1, len(components)):
        comp = list(components[i])
        comp_coords = np.radians([[float(node.split('_')[0]), float(node.split('_')[1])] for node in comp])
        
        distances, indices = tree.query(comp_coords, k=1)
        
        min_idx = np.argmin(distances)
        comp_node_idx = min_idx
        main_node_idx = indices[min_idx][0]
        
        comp_node = comp[comp_node_idx]
        main_node = main_component[main_node_idx]
        
        dist_m = distances[comp_node_idx][0] * EARTH_RADIUS_M
        
        risk_u = G.nodes[comp_node].get('risk', 0)
        risk_v = G.nodes[main_node].get('risk', 0)
        avg_risk = (risk_u + risk_v) / 2
        
        w_safe = dist_m * (1 + risk_weight * avg_risk)
        w_fast = dist_m
        
        G.add_edge(comp_node, main_node, weight_safe=w_safe, weight_fast=w_fast, distance=dist_m)
        
    return G

def build_risk_graph(df_source, EARTH_RADIUS_M, risk_col="risk_score", risk_weight=2.0, k_neighbors=8):
    G = nx.Graph()
    
    # 1. Faster node extraction (no iterrows)
    coords = df_source[['lat_r', 'lon_r']].values
    nodes = df_source['cell_id'].values.tolist()
    risks = df_source[risk_col].values
    
    # Add all nodes instantly
    G.add_nodes_from([
        (node, {"lat": lat, "lon": lon, "risk": risk}) 
        for node, lat, lon, risk in zip(nodes, coords[:,0], coords[:,1], risks)
    ])
    
    if len(nodes) == 0:
        return G
        
    coords_rad = np.radians(coords)
    tree = BallTree(coords_rad, metric='haversine')
    
    k = min(k_neighbors + 1, len(nodes))
    distances, indices = tree.query(coords_rad, k=k)
    
    # 2. Faster edge creation (build list then add_edges_from)
    edges = []
    for i in range(len(nodes)):
        node_u = nodes[i]
        risk_u = risks[i]
        for j in range(1, k):
            idx_v = indices[i, j]
            if i < idx_v: # Avoid duplicates (undirected)
                node_v = nodes[idx_v]
                dist_m = distances[i, j] * EARTH_RADIUS_M
                risk_v = risks[idx_v]
                avg_risk = (risk_u + risk_v) / 2
                
                w_safe = dist_m * (1 + risk_weight * avg_risk)
                w_fast = dist_m
                
                edges.append((node_u, node_v, {'weight_safe': w_safe, 'weight_fast': w_fast, 'distance': dist_m}))
                
    G.add_edges_from(edges)
    G = connect_components(G, None, EARTH_RADIUS_M, risk_weight)
    return G


def load_artifacts():
    logger.info("Loading ML artifacts...")
    EARTH_RADIUS_M = 6371000
    
    import sys
    from sklearn._loss import _loss as _sklearn_loss_module
    
    # Workaround: beberapa build sklearn lama nyimpen __module__ loss class
    # sebagai "_loss" (bukan "sklearn._loss._loss") saat pickling — trik ini
    # nge-alias supaya unpickler nemu module yang dimaksud.
    sys.modules["_loss"] = _sklearn_loss_module
    
    import warnings
    from sklearn.exceptions import InconsistentVersionWarning
    warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
    
    champion_model = joblib.load(os.path.join(ARTIFACTS_DIR, "champion_model.joblib"))
    model_context = joblib.load(os.path.join(ARTIFACTS_DIR, "model_context.joblib"))
    cell_hist_lookup = joblib.load(os.path.join(ARTIFACTS_DIR, "cell_hist_lookup.joblib"))
    
    # Handle the fact that joblib might be returning a dict for cell_hist_lookup
    if isinstance(cell_hist_lookup, dict) and 'cell_hist_lookup' in cell_hist_lookup:
        cell_hist_lookup = cell_hist_lookup['cell_hist_lookup']
        
    remap_bounds = joblib.load(os.path.join(ARTIFACTS_DIR, "remap_bounds.joblib"))
    
    # We now load the pre-built risk_graph.joblib instead of building it from scratch during startup!
    risk_graph = joblib.load(os.path.join(ARTIFACTS_DIR, "risk_graph.joblib"))
    
    safe_places_df = pd.read_csv(os.path.join(ARTIFACTS_DIR, "safe_places.csv"))
    
    if 'lat_r' in cell_hist_lookup.columns and 'lon_r' in cell_hist_lookup.columns:
        cell_coords = np.radians(cell_hist_lookup[['lat_r', 'lon_r']].values)
    else:
        cell_coords = np.radians([
            [float(cid.split('_')[0]), float(cid.split('_')[1])] 
            for cid in cell_hist_lookup['cell_id']
        ])
    cell_hist_tree = BallTree(cell_coords, metric='haversine')
    
    safe_place_coords = np.radians(safe_places_df[['lat', 'lon']].values)
    safe_place_tree = BallTree(safe_place_coords, metric='haversine')
    
    logger.info("ML artifacts loaded successfully.")
    
    return {
        "champion_model": champion_model,
        "model_context": model_context,
        "cell_hist_lookup": cell_hist_lookup,
        "remap_bounds": remap_bounds,
        "cell_hist_tree": cell_hist_tree,
        "safe_places_df": safe_places_df,
        "safe_place_tree": safe_place_tree,
        "risk_graph": risk_graph,
        "EARTH_RADIUS_M": EARTH_RADIUS_M
    }
