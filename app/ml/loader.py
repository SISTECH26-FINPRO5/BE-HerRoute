import os
import joblib
import pandas as pd
import numpy as np
import networkx as nx
from sklearn.neighbors import BallTree
import logging

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "artifacts")




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
