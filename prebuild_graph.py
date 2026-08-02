import joblib
import pandas as pd
import numpy as np
import networkx as nx
from sklearn.neighbors import BallTree
import os
import sys
from sklearn._loss import _loss as _sklearn_loss_module
sys.modules["_loss"] = _sklearn_loss_module

def connect_components(G, cell_risk, EARTH_RADIUS_M, risk_weight=2.0):
    components = list(nx.connected_components(G))
    if len(components) <= 1:
        return G
    components.sort(key=len, reverse=True)
    main_component = list(components[0])
    main_coords = np.radians([[float(node.split('_')[0]), float(node.split('_')[1])] for node in main_component])
    tree = BallTree(main_coords, metric='haversine')
    
    for i in range(1, len(components)):
        comp = list(components[i])
        comp_coords = np.radians([[float(node.split('_')[0]), float(node.split('_')[1])] for node in comp])
        distances, indices = tree.query(comp_coords, k=1)
        min_idx = np.argmin(distances)
        comp_node = comp[min_idx]
        main_node = main_component[indices[min_idx][0]]
        dist_m = distances[min_idx][0] * EARTH_RADIUS_M
        risk_u = G.nodes[comp_node].get('risk', 0)
        risk_v = G.nodes[main_node].get('risk', 0)
        avg_risk = (risk_u + risk_v) / 2
        w_safe = dist_m * (1 + risk_weight * avg_risk)
        w_fast = dist_m
        G.add_edge(comp_node, main_node, weight_safe=w_safe, weight_fast=w_fast, distance=dist_m)
    return G

def build_risk_graph(df_source, EARTH_RADIUS_M, risk_col="risk_score", risk_weight=2.0, k_neighbors=8):
    G = nx.Graph()
    coords = df_source[['lat_r', 'lon_r']].values
    nodes = df_source['cell_id'].values.tolist()
    risks = df_source[risk_col].values
    G.add_nodes_from([(node, {"lat": lat, "lon": lon, "risk": risk}) for node, lat, lon, risk in zip(nodes, coords[:,0], coords[:,1], risks)])
    if len(nodes) == 0: return G
    coords_rad = np.radians(coords)
    tree = BallTree(coords_rad, metric='haversine')
    k = min(k_neighbors + 1, len(nodes))
    distances, indices = tree.query(coords_rad, k=k)
    edges = []
    for i in range(len(nodes)):
        node_u = nodes[i]
        risk_u = risks[i]
        for j in range(1, k):
            idx_v = indices[i, j]
            if i < idx_v:
                node_v = nodes[idx_v]
                dist_m = distances[i, j] * EARTH_RADIUS_M
                risk_v = risks[idx_v]
                avg_risk = (risk_u + risk_v) / 2
                edges.append((node_u, node_v, {'weight_safe': dist_m * (1 + risk_weight * avg_risk), 'weight_fast': dist_m, 'distance': dist_m}))
    G.add_edges_from(edges)
    return connect_components(G, None, EARTH_RADIUS_M, risk_weight)

print("Loading raw data...")
EARTH_RADIUS_M = 6371000
risk_graph_source = joblib.load("artifacts/risk_graph_source.joblib")
df = risk_graph_source['df_for_graph'] if isinstance(risk_graph_source, dict) and 'df_for_graph' in risk_graph_source else risk_graph_source
print("Building graph... (This may take a minute, please wait)")
G = build_risk_graph(df, EARTH_RADIUS_M)
print("Graph built! Saving to artifacts/risk_graph.joblib...")
joblib.dump(G, "artifacts/risk_graph.joblib")
print("Done! You can now start the server instantly.")
