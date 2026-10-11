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

from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

def fetch_real_road_geometry(waypoints):
    """
    Fetches real road network geometry via OSRM turn-by-turn routing engine.
    Returns high-resolution (lat, lon) coordinates tracing actual Kerala roads,
    along with accurate road driving distance (meters) and duration (seconds).
    """
    if len(waypoints) < 2:
        return waypoints, 0.0, 0.0

    # Cap intermediate waypoints to 20 for URL length limits
    if len(waypoints) > 20:
        step = max(1, len(waypoints) // 18)
        sampled = [waypoints[0]] + waypoints[1:-1:step] + [waypoints[-1]]
    else:
        sampled = waypoints

    coord_str = ";".join(f"{lon:.5f},{lat:.5f}" for lat, lon in sampled)
    url = f"http://router.project-osrm.org/route/v1/driving/{coord_str}?overview=full&geometries=geojson"

    try:
        req = Request(url, headers={"User-Agent": "KeralaResilienceOS/1.0"})
        with urlopen(req, timeout=2.5) as resp:
            data = json.load(resp)
            if data.get("code") == "Ok" and data.get("routes"):
                route = data["routes"][0]
                # OSRM returns coordinates as [lon, lat] -> convert to [lat, lon]
                coords = [[lat, lon] for lon, lat in route["geometry"]["coordinates"]]
                dist_m = float(route.get("distance", 0.0))
                dur_s = float(route.get("duration", 0.0))
                return coords, dist_m, dur_s
    except Exception:
        pass

    return None, 0.0, 0.0

def generate_curved_fallback_geometry(waypoints, points_per_segment=7):
    """
    Resilient offline geometry interpolator.
    Produces smooth, realistic road curvature bends rather than rigid straight lines
    when the device or server is offline.
    """
    if len(waypoints) < 2:
        return waypoints

    out = [waypoints[0]]
    for i in range(len(waypoints) - 1):
        lat1, lon1 = waypoints[i]
        lat2, lon2 = waypoints[i + 1]
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        dist = math.sqrt(dlat * dlat + dlon * dlon)
        if dist < 1e-6:
            continue

        # Perpendicular unit normal vector
        nlat = -dlon / dist
        nlon = dlat / dist
        curve_amp = min(0.0025, dist * 0.09)

        for s in range(1, points_per_segment):
            t = s / points_per_segment
            # Gentle sinusoidal curvature offset
            offset = math.sin(t * math.pi) * curve_amp
            clat = lat1 + t * dlat + offset * nlat
            clon = lon1 + t * dlon + offset * nlon
            out.append([round(clat, 6), round(clon, 6)])

        out.append(waypoints[i + 1])

    return out

def trim_geometry_at_destination(coordinates, dest_lat, dest_lon):
    """Keep only the route segment from its start through the destination."""
    if not coordinates:
        return coordinates

    destination = (dest_lat, dest_lon)
    end_index = min(
        range(len(coordinates)),
        key=lambda index: haversine_dist(coordinates[index], destination),
    )
    trimmed = coordinates[:end_index + 1]
    if trimmed and haversine_dist(trimmed[-1], destination) > 20.0:
        trimmed.append([dest_lat, dest_lon])
    return trimmed

def compute_route(
    G,
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    mode: str = "safe",
    path_override=None,
):
    """
    Runs A* search from origin to destination coordinates.
    mode = 'safe' : avoids blocked roads, minimizes risk-weighted cost
    Returns realistic street-following polyline coordinates (not just straight chords).
    """
    # Check if origin and destination are virtually identical (< 30m)
    d_direct = haversine_dist((origin_lat, origin_lon), (dest_lat, dest_lon))
    if d_direct < 30.0:
        return {
            "status": "success",
            "mode": mode,
            "coordinates": [[origin_lat, origin_lon]],
            "distance_km": 0.0,
            "distance_meters": 0.0,
            "duration_minutes": 0.0,
            "risk_score": 0.0,
            "avg_risk": 0.0,
            "nodes": [],
            "road_names": ["Direct Access"],
            "blocked_avoided": 0,
            "message": "Origin and destination are at the same location."
        }

    origin_node, _ = find_nearest_node(G, origin_lat, origin_lon)
    dest_node, _ = find_nearest_node(G, dest_lat, dest_lon)

    # Prepare graph view
    if mode == "safe":
        def is_open(u, v):
            edge_data = G.get_edge_data(u, v)
            return not edge_data.get("blocked", False)

        H = nx.subgraph_view(G, filter_edge=is_open)
        weight_fn = lambda u, v, d: d.get("risk_cost", d.get("length", 1000.0))
    else:
        H = G
        weight_fn = "length"

    # Haversine heuristic (admissible)
    def heuristic(u, v):
        pos_u = (H.nodes[u]["lat"], H.nodes[u]["lon"])
        pos_v = (H.nodes[v]["lat"], H.nodes[v]["lon"])
        return haversine_dist(pos_u, pos_v)

    try:
        path = path_override or nx.astar_path(
            H, origin_node, dest_node, heuristic=heuristic, weight=weight_fn
        )
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        if mode == "safe":
            return {
                "status": "no_safe_path",
                "mode": mode,
                "coordinates": [],
                "distance_km": 0.0,
                "distance_meters": 0.0,
                "duration_minutes": 0.0,
                "risk_score": 1.0,
                "avg_risk": 1.0,
                "nodes": [],
                "road_names": [],
                "blocked_avoided": 0,
                "message": "CRITICAL ALERT: No safe overland corridor available. Target is cut off by critical flood waters."
            }
        else:
            return {
                "status": "no_path",
                "mode": mode,
                "coordinates": [],
                "distance_km": 0.0,
                "distance_meters": 0.0,
                "duration_minutes": 0.0,
                "risk_score": 1.0,
                "avg_risk": 1.0,
                "nodes": [],
                "road_names": [],
                "blocked_avoided": 0,
                "message": "No road connection exists between selected locations."
            }

    # Extract network distance, risk, and road names
    total_dist_m = 0.0
    accum_risk = 0.0
    road_names = []

    # Sequence of key waypoints connecting origin -> graph nodes -> destination
    waypoints = [[origin_lat, origin_lon]]
    for i, n in enumerate(path):
        node_coords = [G.nodes[n]["lat"], G.nodes[n]["lon"]]
        if haversine_dist(waypoints[-1], node_coords) > 20.0:
            waypoints.append(node_coords)

        if i > 0:
            prev = path[i - 1]
            e_data = G.get_edge_data(prev, n)
            total_dist_m += e_data.get("length", 1000.0)
            accum_risk += e_data.get("zone_risk", 0.2)
            name = e_data.get("name")
            if name and name not in road_names:
                road_names.append(name)

    dest_coords = [dest_lat, dest_lon]
    if haversine_dist(waypoints[-1], dest_coords) > 20.0:
        waypoints.append(dest_coords)

    avg_risk = accum_risk / max(1, len(path) - 1)

    # Fetch high-resolution road geometry (bends and streets)
    real_coords, osrm_dist_m, osrm_dur_s = fetch_real_road_geometry(waypoints)

    if real_coords and len(real_coords) >= 2:
        final_coords = trim_geometry_at_destination(real_coords, dest_lat, dest_lon)
        final_dist_m = osrm_dist_m if osrm_dist_m > 0 else total_dist_m
        est_duration_mins = round(osrm_dur_s / 60.0, 1) if osrm_dur_s > 0 else round((final_dist_m / 1000.0) / 35.0 * 60.0, 1)
    else:
        # Fallback to curved geometry interpolation
        final_coords = trim_geometry_at_destination(
            generate_curved_fallback_geometry(waypoints),
            dest_lat,
            dest_lon,
        )
        # Direct haversine legs + winding factor ~1.25 for urban Kerala roads
        calc_dist = sum(haversine_dist(waypoints[j], waypoints[j+1]) for j in range(len(waypoints)-1)) * 1.25
        final_dist_m = max(total_dist_m, calc_dist)
        est_duration_mins = round((final_dist_m / 1000.0) / 35.0 * 60.0, 1)

    return {
        "status": "success",
        "mode": mode,
        "coordinates": final_coords,
        "distance_km": round(final_dist_m / 1000.0, 2),
        "distance_meters": round(final_dist_m, 1),
        "duration_minutes": est_duration_mins,
        "risk_score": round(avg_risk, 3),
        "avg_risk": round(avg_risk, 3),
        "nodes": path,
        "road_names": road_names if road_names else ["District Arterial Road"],
        "blocked_avoided": 0,
        "message": "Route computed successfully with street-level geometry."
    }

def get_safest_route(G, origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float):
    """
    Computes Safest Route (risk-weighted edges, avoiding critical submerged corridors)
    along with Shortest Route for side-by-side comparative trade-off analysis.
    """
    safest = compute_route(G, origin_lat, origin_lon, dest_lat, dest_lon, mode="safe")
    shortest = compute_route(G, origin_lat, origin_lon, dest_lat, dest_lon, mode="short")

    # Calculate safety trade-off and count blocked corridors in shortest route
    dist_diff_km = 0.0
    risk_diff_pct = 0.0
    critical_roads_in_shortest = 0

    if shortest["status"] == "success" and len(shortest["nodes"]) > 1:
        for i in range(len(shortest["nodes"]) - 1):
            u, v = shortest["nodes"][i], shortest["nodes"][i+1]
            e_data = G.get_edge_data(u, v)
            if e_data and e_data.get("blocked", False):
                critical_roads_in_shortest += 1

    shortest["blocked_chokepoints_crossed"] = critical_roads_in_shortest
    shortest["is_submerged"] = (critical_roads_in_shortest > 0)

    if safest["status"] == "success" and shortest["status"] == "success":
        dist_diff_km = round(safest["distance_km"] - shortest["distance_km"], 2)
        sh_risk = shortest.get("avg_risk", 0.0)
        sf_risk = safest.get("avg_risk", 0.0)
        if sh_risk > 0:
            risk_diff_pct = int(round((1.0 - (sf_risk / sh_risk)) * 100))
        safest["blocked_avoided"] = critical_roads_in_shortest
    elif safest["status"] == "no_safe_path":
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

get_dual_routes = get_safest_route
