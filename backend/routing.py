"""
Safe Routing with A* Search (Module 5)
Computes Safest Route (risk-weighted edges, critical roads blocked)
vs Shortest Route (raw physical distance).
"""
import os
import json
import math
import networkx as nx
from backend.config import ROAD_GRAPH_GRAPHML, ROAD_GRAPH_JSON, ROUTING_PENALTY_K

def haversine_dist(a, b):
    """Haversine distance in meters between (lat1, lon1) and (lat2, lon2)"""
    R = 6371000.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2.0)**2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2.0)**2
    return 2.0 * R * math.asin(math.sqrt(h))

def load_graph():
    """Loads NetworkX graph from graphml or json fallback"""
    if os.path.exists(ROAD_GRAPH_GRAPHML):
        G = nx.read_graphml(ROAD_GRAPH_GRAPHML)
        # Ensure lat and lon are floats
        for n, d in G.nodes(data=True):
            d["lat"] = float(d.get("lat", 0.0))
            d["lon"] = float(d.get("lon", 0.0))
        for u, v, d in G.edges(data=True):
            d["length"] = float(d.get("length", 1000.0))
        return G

    # Fallback to json
    with open(ROAD_GRAPH_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    G = nx.Graph()
    for nid, d in data["nodes"].items():
        G.add_node(nid, **d)
    for e in data["edges"]:
        G.add_edge(e["u"], e["v"], name=e["name"], length=float(e["length"]), zone_id=e["zone_id"])
    return G

G = load_graph()

def find_nearest_node(G, lat: float, lon: float):
    """Finds closest node in the road network to given coordinates"""
    best_node = None
    best_dist = float("inf")
    for n, data in G.nodes(data=True):
        d = haversine_dist((lat, lon), (data["lat"], data["lon"]))
        if d < best_dist:
            best_dist = d
            best_node = n
    return best_node, best_dist

def apply_risk(G, zone_risk: dict, zone_class: dict, k: float = ROUTING_PENALTY_K):
    """
    Updates edge costs:
      - Block edges passing through critical zones
      - Multiply edge cost by (1 + k * zone_risk)
    """
    for u, v, data in G.edges(data=True):
        zid = data.get("zone_id")
        r = float(zone_risk.get(zid, 0.2))
        zc = zone_class.get(zid, "low")

        data["blocked"] = (zc == "critical")
        data["risk_cost"] = float(data["length"]) * (1.0 + k * r)
        data["zone_risk"] = r
        data["zone_class"] = zc

def compute_route(G, origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float, mode: str = "safe"):
    """
    Runs A* search from origin to destination coordinates.
    mode = 'safe' : avoids blocked roads, minimizes risk-weighted cost
    mode = 'short': uses full road network, minimizes raw physical distance
    """
    origin_node, _ = find_nearest_node(G, origin_lat, origin_lon)
    dest_node, _ = find_nearest_node(G, dest_lat, dest_lon)

    if origin_node == dest_node:
        n_data = G.nodes[origin_node]
        return {
            "status": "success",
            "mode": mode,
            "coordinates": [[n_data["lat"], n_data["lon"]]],
            "distance_km": 0.0,
            "distance_meters": 0.0,
            "risk_score": 0.0,
            "avg_risk": 0.0,
            "nodes": [origin_node],
            "road_names": [],
            "blocked_avoided": 0,
            "message": "Origin and destination are at the same junction."
        }

    # Prepare graph view
    if mode == "safe":
        # Filter out blocked roads
        def is_open(u, v):
            edge_data = G.get_edge_data(u, v)
            return not edge_data.get("blocked", False)

        H = nx.subgraph_view(G, filter_edge=is_open)
        weight_fn = lambda u, v, d: d.get("risk_cost", d.get("length", 1000.0))
    else:
        H = G
        weight_fn = "length"

    # Haversine heuristic (admissible since straight line <= road length <= risk_cost)
    def heuristic(u, v):
        pos_u = (H.nodes[u]["lat"], H.nodes[u]["lon"])
        pos_v = (H.nodes[v]["lat"], H.nodes[v]["lon"])
        return haversine_dist(pos_u, pos_v)

    try:
        path = nx.astar_path(H, origin_node, dest_node, heuristic=heuristic, weight=weight_fn)
    except nx.NetworkXNoPath:
        if mode == "safe":
            return {
                "status": "no_safe_path",
                "mode": mode,
                "coordinates": [],
                "distance_km": 0.0,
                "risk_score": 1.0,
                "nodes": [],
                "road_names": [],
                "blocked_avoided": 0,
                "message": "CRITICAL ALERT: No safe corridor available. Destination cut off by critical flood inundation."
            }
        else:
            return {
                "status": "no_path",
                "mode": mode,
                "coordinates": [],
                "distance_km": 0.0,
                "risk_score": 1.0,
                "nodes": [],
                "road_names": [],
                "blocked_avoided": 0,
                "message": "No road connection exists between selected locations."
            }

    # Extract path coordinates, total distance, and risk
    coords = []
    total_dist_m = 0.0
    accum_risk = 0.0
    road_names = []
    blocked_avoided = 0

    for i, n in enumerate(path):
        coords.append([G.nodes[n]["lat"], G.nodes[n]["lon"]])
        if i > 0:
            prev = path[i - 1]
            e_data = G.get_edge_data(prev, n)
            total_dist_m += e_data.get("length", 0.0)
            accum_risk += e_data.get("zone_risk", 0.2)
            name = e_data.get("name")
            if name and name not in road_names:
                road_names.append(name)

    avg_risk = accum_risk / max(1, len(path) - 1)

    return {
        "status": "success",
        "mode": mode,
        "coordinates": coords,
        "distance_km": round(total_dist_m / 1000.0, 2),
        "distance_meters": round(total_dist_m, 1),
        "avg_risk": round(avg_risk, 3),
        "nodes": path,
        "road_names": road_names,
        "blocked_avoided": blocked_avoided,
        "message": "Route computed successfully."
    }

def get_dual_routes(G, origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float):
    """
    Computes both Safest and Shortest routes and returns side-by-side trade-off comparison.
    """
    safest = compute_route(G, origin_lat, origin_lon, dest_lat, dest_lon, mode="safe")
    shortest = compute_route(G, origin_lat, origin_lon, dest_lat, dest_lon, mode="short")

    # Calculate safety trade-off
    dist_diff_km = 0.0
    risk_diff_pct = 0.0
    critical_roads_in_shortest = 0

    if shortest["status"] == "success":
        for i in range(len(shortest["nodes"]) - 1):
            u, v = shortest["nodes"][i], shortest["nodes"][i+1]
            e_data = G.get_edge_data(u, v)
            if e_data.get("blocked", False):
                critical_roads_in_shortest += 1

    if safest["status"] == "success" and shortest["status"] == "success":
        dist_diff_km = round(safest["distance_km"] - shortest["distance_km"], 2)
        sh_risk = shortest.get("avg_risk", 0.0)
        sf_risk = safest.get("avg_risk", 0.0)
        if sh_risk > 0:
            risk_diff_pct = int(round((1.0 - (sf_risk / sh_risk)) * 100))
    elif safest["status"] == "no_safe_path":
        # Destination cut off by critical flood - emergency warning flag
        dist_diff_km = 0.0
        risk_diff_pct = 0

    return {
        "safest": safest,
        "shortest": shortest,
        "tradeoff": {
            "extra_distance_km": max(0.0, dist_diff_km),
            "risk_reduction_pct": max(0, risk_diff_pct),
            "critical_chokepoints_avoided": critical_roads_in_shortest
        }
    }
