"""
Build Features and Processed Data for Kerala Resilience OS (Ernakulam District)
Generates:
  - data/processed/zones_features.csv
  - data/processed/zones.geojson
  - data/processed/hospitals.csv
  - data/processed/schools.csv
  - data/processed/road_graph.json and road_graph.graphml
  - data/processed/affected_places.json
"""
import os
import json
import math
import numpy as np
import pandas as pd
import networkx as nx

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(DATA_DIR, exist_ok=True)

# 10 Key Strategic Zones of Ernakulam District
# Grounded in Kerala 2018 Post Disaster Needs Assessment (PDNA) & Ernakulam topography
ZONES_DATA = [
    {
        "zone_id": "Z01",
        "name": "Aluva",
        "lat": 10.1076,
        "lon": 76.3516,
        "hist_risk": 0.95,       # Epicenter of 2018 Periyar overflow
        "elevation_m": 8.0,      # Low elevation along riverbank
        "terrain": 0.88,         # Highly vulnerable riverine basin
        "road_vuln": 0.85,       # NH 544 bridges & low lying service roads
        "river_prox": 0.98,      # Directly straddles Periyar river
        "n_hospitals": 6,
        "n_schools": 16,
        "places": {
            "Evacuation": "Aluva Manappuram, Bank Junction, Thottakkattukara, Desom Colony",
            "Open shelters": "UC College Aluva, St. Xavier's College, Govt Girls HSS Aluva",
            "Deploy pumps": "Aluva Private Bus Stand, Railway Station Subway, Market Road",
            "Close roads": "Aluva Marthanda Varma Old Bridge, Aluva-Paravur Road Causeway",
            "Alert hospitals": "Aluva District Hospital, Karothukuzhi Hospital, Najath Hospital",
            "Public alert": "Periyar River Basin wards 1-14, Municipal Colony, Kunnumpuram"
        },
        # Polygon boundary around Aluva
        "polygon": [
            [76.320, 10.135], [76.375, 10.140], [76.390, 10.105],
            [76.365, 10.075], [76.325, 10.085], [76.320, 10.135]
        ]
    },
    {
        "zone_id": "Z02",
        "name": "North Paravur",
        "lat": 10.1455,
        "lon": 76.2301,
        "hist_risk": 0.90,       # Severe flooding & sea-river confluence in 2018
        "elevation_m": 4.0,      # Near sea level
        "terrain": 0.92,         # Coastal wetlands & backwater network
        "road_vuln": 0.82,       # Coastal highways & causeways
        "river_prox": 0.88,      # Lower Periyar delta & Vembanad channels
        "n_hospitals": 5,
        "n_schools": 14,
        "places": {
            "Evacuation": "Chendamangalam Weavers Colony, Varapuzha Island, Kottuvally Lowlands",
            "Open shelters": "Paravur Govt Boys HSS, SNM College Maliankara, St. Aloysius School",
            "Deploy pumps": "Paravur Municipal Market, Kacheri Thazham, KMK Junction",
            "Close roads": "Varapuzha Bridge Approaches, Paravur-Aluva Coastal Link",
            "Alert hospitals": "Paravur Taluk Headquarters Hospital, Don Bosco Hospital",
            "Public alert": "Chendamangalam, Ezhikkara, Chittattukara coastal settlements"
        },
        "polygon": [
            [76.195, 10.170], [76.265, 10.175], [76.280, 10.120],
            [76.220, 10.105], [76.195, 10.170]
        ]
    },
    {
        "zone_id": "Z03",
        "name": "Kanayannur (Ernakulam City)",
        "lat": 9.9816,
        "lon": 76.2999,
        "hist_risk": 0.72,       # Urban waterlogging & backwater surge
        "elevation_m": 5.0,
        "terrain": 0.75,         # Flat urban, tidal canals (Mullassery canal)
        "road_vuln": 0.70,       # MG Road, South Overbridge, KSRTC bus stand
        "river_prox": 0.55,      # Backwater tidal influence
        "n_hospitals": 12,
        "n_schools": 22,
        "places": {
            "Evacuation": "P&T Colony Kadavanthra, Udaya Colony, Thammanam canal belt",
            "Open shelters": "Maharajas College Hostel, St. Albert's College, St. Teresa's",
            "Deploy pumps": "KSRTC Central Bus Stand, South Railway Station Subway, MG Road",
            "Close roads": "Mullassery Canal Road, Kaloor-Kadavanthra Underpass",
            "Alert hospitals": "Ernakulam General Hospital, Medical Trust Hospital, Lisie Hospital",
            "Public alert": "Ernakulam Central, Panampilly Nagar, Ravipuram, Kaloor wards"
        },
        "polygon": [
            [76.270, 10.020], [76.335, 10.015], [76.340, 9.945],
            [76.275, 9.950], [76.270, 10.020]
        ]
    },
    {
        "zone_id": "Z04",
        "name": "Kochi (Fort Kochi & Mattancherry)",
        "lat": 9.9650,
        "lon": 76.2420,
        "hist_risk": 0.65,       # Tidal flooding & high tide back surge
        "elevation_m": 2.5,      # Very low coastal elevation
        "terrain": 0.85,         # Coastal peninsula & island cluster
        "road_vuln": 0.68,       # Beach road, Bazar road
        "river_prox": 0.45,      # Arabian sea & Cochin estuary mouth
        "n_hospitals": 4,
        "n_schools": 12,
        "places": {
            "Evacuation": "Veli Lowlands, Fort Kochi Beach Settlement, Mattancherry Bazar edge",
            "Open shelters": "Santa Cruz HSS Fort Kochi, TD High School Mattancherry",
            "Deploy pumps": "Mattancherry Spice Market, Calvathy Canal outlet, Fort Kochi Bus Stand",
            "Close roads": "Calvathy Bridge Approaches, Bazar Road tidal strip",
            "Alert hospitals": "Cochin Port Trust Hospital, Fort Kochi Taluk Hospital",
            "Public alert": "Fort Kochi, Mattancherry, Amaravathi, Pandikudy coastal residents"
        },
        "polygon": [
            [76.210, 9.995], [76.265, 9.990], [76.265, 9.930],
            [76.215, 9.935], [76.210, 9.995]
        ]
    },
    {
        "zone_id": "Z05",
        "name": "Kalamassery",
        "lat": 10.0530,
        "lon": 76.3210,
        "hist_risk": 0.70,       # Periyar tributary backflow & industrial corridor
        "elevation_m": 12.0,     # Mixed undulating terrain
        "terrain": 0.60,
        "road_vuln": 0.65,       # Seaport-Airport Road & NH 544
        "river_prox": 0.75,      # Close to Eloor Periyar industrial bend
        "n_hospitals": 7,
        "n_schools": 15,
        "places": {
            "Evacuation": "Eloor Ferry, FACT Township Lowlands, HMT Colony near stream",
            "Open shelters": "CUSAT Student Amenity Centre, Rajagiri College Kalamassery",
            "Deploy pumps": "Container Road Junction, Premier Junction Underpass",
            "Close roads": "Pathalam Bund Road, Eloor Industrial Link Bridge",
            "Alert hospitals": "Govt Medical College Ernakulam (Kalamassery), Apollo Adlux Clinic",
            "Public alert": "Eloor Municipality, Kalamassery Ward 10-22, South Kalamassery"
        },
        "polygon": [
            [76.285, 10.080], [76.350, 10.080], [76.355, 10.025],
            [76.280, 10.030], [76.285, 10.080]
        ]
    },
    {
        "zone_id": "Z06",
        "name": "Kunnathunad (Perumbavoor)",
        "lat": 10.1115,
        "lon": 76.4780,
        "hist_risk": 0.78,       # Significant riverine inundation along Periyar curve
        "elevation_m": 18.0,
        "terrain": 0.55,         # Midland undulating agricultural & river plain
        "road_vuln": 0.62,       # MC Road & Perumbavoor junctions
        "river_prox": 0.82,      # Periyar river passes right through
        "n_hospitals": 5,
        "n_schools": 18,
        "places": {
            "Evacuation": "Kalady Sringeri Ghats, Okkal Colony, Vallam Rayonpuram flood zone",
            "Open shelters": "Asramam HSS Perumbavoor, Sree Sankara College Kalady",
            "Deploy pumps": "Perumbavoor Private Bus Stand, Kalady Junction Market",
            "Close roads": "Kalady Bridge over Periyar, MC Road Mattoor stretch",
            "Alert hospitals": "Sanjo Hospital Perumbavoor, Taluk Hospital Perumbavoor",
            "Public alert": "Kalady, Okkal, Koovappady, Rayonpuram riverside settlements"
        },
        "polygon": [
            [76.410, 10.160], [76.540, 10.155], [76.535, 10.060],
            [76.405, 10.070], [76.410, 10.160]
        ]
    },
    {
        "zone_id": "Z07",
        "name": "Muvattupuzha",
        "lat": 9.9830,
        "lon": 76.5800,
        "hist_risk": 0.62,       # Three rivers meet (Thodupuzha, Kaliyar, Kothamangalam)
        "elevation_m": 22.0,
        "terrain": 0.50,         # Midland hills with river confluence bottlenecks
        "road_vuln": 0.58,       # MC Road bridges & riverside shops
        "river_prox": 0.80,      # Muvattupuzha river confluence
        "n_hospitals": 5,
        "n_schools": 15,
        "places": {
            "Evacuation": "Tribeni Sangamam confluence, Kacherithazham riverside, Kadathy",
            "Open shelters": "NSS HSS Muvattupuzha, Nirmala College Muvattupuzha",
            "Deploy pumps": "Kacherithazham Bridge Sub-road, Municipal Market",
            "Close roads": "Velloorkunnam Low Bridge, Thodupuzha Road Riverside link",
            "Alert hospitals": "Muvattupuzha General Hospital, Nirmala Medical Centre",
            "Public alert": "Muvattupuzha riverside wards, Marady, Arakuzha settlements"
        },
        "polygon": [
            [76.510, 10.050], [76.650, 10.040], [76.640, 9.920],
            [76.505, 9.930], [76.510, 10.050]
        ]
    },
    {
        "zone_id": "Z08",
        "name": "Kothamangalam",
        "lat": 10.0620,
        "lon": 76.6320,
        "hist_risk": 0.38,       # Western Ghats foothills, flash flood runoff
        "elevation_m": 55.0,     # Elevated foothill terrain
        "terrain": 0.35,         # Hilly, steep gradient runoff
        "road_vuln": 0.40,       # Hill roads, ghat bridges
        "river_prox": 0.60,      # Upper tributaries of Periyar & Kaliyar
        "n_hospitals": 4,
        "n_schools": 14,
        "places": {
            "Evacuation": "Bhoothathankettu downstream tribal settlements, Keerampara river edge",
            "Open shelters": "Mar Athanasius College Kothamangalam, St. George HSS",
            "Deploy pumps": "Kothamangalam Town Bus Stand, Post Office Junction",
            "Close roads": "Bhoothathankettu Barrage Access Road, Chelad Bridge",
            "Alert hospitals": "Mar Baselios Medical Mission Hospital, Taluk Hospital Kothamangalam",
            "Public alert": "Kothamangalam, Pothanicad, Varappetty foothill valleys"
        },
        "polygon": [
            [76.560, 10.150], [76.750, 10.140], [76.730, 9.980],
            [76.565, 10.000], [76.560, 10.150]
        ]
    },
    {
        "zone_id": "Z09",
        "name": "Angamaly",
        "lat": 10.1960,
        "lon": 76.3860,
        "hist_risk": 0.80,       # CIAL Cochin Airport & northern Periyar distributary
        "elevation_m": 14.0,
        "terrain": 0.65,         # Flood basin near airport canal (Chengalthodu)
        "road_vuln": 0.78,       # NH 544 & Airport road
        "river_prox": 0.80,      # Close to Chengalthodu & Periyar north bank
        "n_hospitals": 5,
        "n_schools": 14,
        "places": {
            "Evacuation": "Airport periphery Chengalthodu basin, Nayathode, Mattoor colony",
            "Open shelters": "De Paul Institute Angamaly, St. Joseph's Girls HSS",
            "Deploy pumps": "Angamaly KSRTC Bus Stand, Airport Runway Drainage Channel",
            "Close roads": "VIP Road towards CIAL, Angamaly Town Underpass",
            "Alert hospitals": "Little Flower Hospital & Research Centre Angamaly, TELK Clinic",
            "Public alert": "Angamaly Municipality, Nedumbassery, Chengamanad wards"
        },
        "polygon": [
            [76.340, 10.250], [76.440, 10.245], [76.435, 10.150],
            [76.330, 10.155], [76.340, 10.250]
        ]
    },
    {
        "zone_id": "Z10",
        "name": "Tripunithura",
        "lat": 9.9480,
        "lon": 76.3480,
        "hist_risk": 0.58,       # South Ernakulam backwater canals
        "elevation_m": 7.0,
        "terrain": 0.70,         # Low-lying backwater basin
        "road_vuln": 0.60,       # Hill Palace Road, mini bypass
        "river_prox": 0.52,      # Chambakkara & Chitrapuzha canals
        "n_hospitals": 4,
        "n_schools": 12,
        "places": {
            "Evacuation": "Chitrapuzha canal bank, Irumpanam refinery periphery, Puthiyakavu lowlands",
            "Open shelters": "Govt Sanskrit College Tripunithura, Palace Girls HSS",
            "Deploy pumps": "Statue Junction, Tripunithura Railway Station Road",
            "Close roads": "Chambakkara Bridge approach, Iron Bridge road",
            "Alert hospitals": "Taluk Hospital Tripunithura, Varma Hospital",
            "Public alert": "Tripunithura, Maradu, Udayamperoor canal belt residents"
        },
        "polygon": [
            [76.315, 9.970], [76.395, 9.965], [76.390, 9.900],
            [76.310, 9.910], [76.315, 9.970]
        ]
    }
]

def build_features_and_geo():
    print("Building zones feature table and GeoJSON...")
    elev_vals = [z["elevation_m"] for z in ZONES_DATA]
    elev_min = min(elev_vals)
    elev_max = max(elev_vals)

    rows = []
    geojson_features = []
    affected_places = {}

    for z in ZONES_DATA:
        elev_norm = (z["elevation_m"] - elev_min) / (elev_max - elev_min)
        rows.append({
            "zone_id": z["zone_id"],
            "name": z["name"],
            "lat": z["lat"],
            "lon": z["lon"],
            "hist_risk": z["hist_risk"],
            "elevation_m": z["elevation_m"],
            "elev_norm": round(elev_norm, 3),
            "terrain": z["terrain"],
            "road_vuln": z["road_vuln"],
            "river_prox": z["river_prox"],
            "n_hospitals": z["n_hospitals"],
            "n_schools": z["n_schools"]
        })
        affected_places[z["zone_id"]] = z["places"]

        # GeoJSON Polygon
        geojson_features.append({
            "type": "Feature",
            "properties": {
                "zone_id": z["zone_id"],
                "name": z["name"],
                "lat": z["lat"],
                "lon": z["lon"],
                "elevation_m": z["elevation_m"],
                "hist_risk": z["hist_risk"],
                "terrain": z["terrain"],
                "river_prox": z["river_prox"],
                "n_hospitals": z["n_hospitals"],
                "n_schools": z["n_schools"]
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [z["polygon"]]
            }
        })

    zones_df = pd.DataFrame(rows)
    zones_csv_path = os.path.join(DATA_DIR, "zones_features.csv")
    zones_df.to_csv(zones_csv_path, index=False)
    print(f"Saved: {zones_csv_path} ({len(zones_df)} zones)")

    geojson_obj = {
        "type": "FeatureCollection",
        "features": geojson_features
    }
    geojson_path = os.path.join(DATA_DIR, "zones.geojson")
    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(geojson_obj, f, indent=2)
    print(f"Saved: {geojson_path}")

    places_path = os.path.join(DATA_DIR, "affected_places.json")
    with open(places_path, "w", encoding="utf-8") as f:
        json.dump(affected_places, f, indent=2)
    print(f"Saved: {places_path}")

def build_facilities():
    print("Building hospitals and schools datasets...")
    # Real Ernakulam emergency hospitals
    hospitals = [
        {"name": "Aluva District Hospital", "lat": 10.1092, "lon": 76.3541, "zone_id": "Z01", "beds": 420, "icu_flooded_risk": "High"},
        {"name": "Karothukuzhi Hospital Aluva", "lat": 10.1130, "lon": 76.3570, "zone_id": "Z01", "beds": 150, "icu_flooded_risk": "High"},
        {"name": "Najath Hospital Aluva", "lat": 10.1020, "lon": 76.3490, "zone_id": "Z01", "beds": 180, "icu_flooded_risk": "Critical"},
        {"name": "Don Bosco Hospital Paravur", "lat": 10.1440, "lon": 76.2290, "zone_id": "Z02", "beds": 160, "icu_flooded_risk": "High"},
        {"name": "Paravur Taluk Headquarters Hospital", "lat": 10.1480, "lon": 76.2340, "zone_id": "Z02", "beds": 250, "icu_flooded_risk": "Critical"},
        {"name": "Ernakulam General Hospital", "lat": 9.9765, "lon": 76.2825, "zone_id": "Z03", "beds": 780, "icu_flooded_risk": "Medium"},
        {"name": "Medical Trust Hospital Kochi", "lat": 9.9680, "lon": 76.2920, "zone_id": "Z03", "beds": 500, "icu_flooded_risk": "Medium"},
        {"name": "Lisie Hospital Kaloor", "lat": 9.9930, "lon": 76.2890, "zone_id": "Z03", "beds": 650, "icu_flooded_risk": "Medium"},
        {"name": "Aster Medcity Cheranallur", "lat": 10.0460, "lon": 76.2750, "zone_id": "Z05", "beds": 670, "icu_flooded_risk": "High"},
        {"name": "Govt Medical College Ernakulam (Kalamassery)", "lat": 10.0545, "lon": 76.3530, "zone_id": "Z05", "beds": 700, "icu_flooded_risk": "Low"},
        {"name": "Fort Kochi Taluk Hospital", "lat": 9.9630, "lon": 76.2440, "zone_id": "Z04", "beds": 140, "icu_flooded_risk": "Medium"},
        {"name": "Sanjo Hospital Perumbavoor", "lat": 10.1140, "lon": 76.4760, "zone_id": "Z06", "beds": 220, "icu_flooded_risk": "High"},
        {"name": "Taluk Hospital Perumbavoor", "lat": 10.1170, "lon": 76.4810, "zone_id": "Z06", "beds": 200, "icu_flooded_risk": "Medium"},
        {"name": "Muvattupuzha General Hospital", "lat": 9.9820, "lon": 76.5780, "zone_id": "Z07", "beds": 350, "icu_flooded_risk": "Medium"},
        {"name": "Nirmala Medical Centre Muvattupuzha", "lat": 9.9780, "lon": 76.5820, "zone_id": "Z07", "beds": 280, "icu_flooded_risk": "Low"},
        {"name": "Mar Baselios Medical Mission Hospital", "lat": 10.0590, "lon": 76.6340, "zone_id": "Z08", "beds": 310, "icu_flooded_risk": "Low"},
        {"name": "Little Flower Hospital Angamaly", "lat": 10.1980, "lon": 76.3880, "zone_id": "Z09", "beds": 610, "icu_flooded_risk": "High"},
        {"name": "Taluk Hospital Tripunithura", "lat": 9.9510, "lon": 76.3510, "zone_id": "Z10", "beds": 190, "icu_flooded_risk": "Medium"}
    ]
    pd.DataFrame(hospitals).to_csv(os.path.join(DATA_DIR, "hospitals.csv"), index=False)

    # Schools / Relief Camps across Ernakulam
    schools = [
        {"name": "UC College Aluva Relief Camp", "lat": 10.1240, "lon": 76.3420, "zone_id": "Z01", "capacity": 1200},
        {"name": "St. Xavier's College for Women Aluva", "lat": 10.1120, "lon": 76.3550, "zone_id": "Z01", "capacity": 900},
        {"name": "Govt Girls HSS Aluva", "lat": 10.1060, "lon": 76.3530, "zone_id": "Z01", "capacity": 600},
        {"name": "SNM College Maliankara Paravur", "lat": 10.1580, "lon": 76.2150, "zone_id": "Z02", "capacity": 1100},
        {"name": "Govt Boys HSS North Paravur", "lat": 10.1460, "lon": 76.2320, "zone_id": "Z02", "capacity": 850},
        {"name": "St. Aloysius HSS Paravur", "lat": 10.1410, "lon": 76.2280, "zone_id": "Z02", "capacity": 700},
        {"name": "Maharajas College Ernakulam", "lat": 9.9730, "lon": 76.2840, "zone_id": "Z03", "capacity": 2000},
        {"name": "St. Albert's College Ernakulam", "lat": 9.9860, "lon": 76.2810, "zone_id": "Z03", "capacity": 1500},
        {"name": "St. Teresa's College Park Avenue", "lat": 9.9790, "lon": 76.2790, "zone_id": "Z03", "capacity": 1300},
        {"name": "Santa Cruz HSS Fort Kochi", "lat": 9.9660, "lon": 76.2410, "zone_id": "Z04", "capacity": 800},
        {"name": "TD High School Mattancherry", "lat": 9.9590, "lon": 76.2510, "zone_id": "Z04", "capacity": 650},
        {"name": "CUSAT Student Amenity Centre", "lat": 10.0440, "lon": 76.3280, "zone_id": "Z05", "capacity": 1800},
        {"name": "Rajagiri College of Social Sciences", "lat": 10.0520, "lon": 76.3180, "zone_id": "Z05", "capacity": 1400},
        {"name": "Sree Sankara College Kalady", "lat": 10.1680, "lon": 76.4390, "zone_id": "Z06", "capacity": 1600},
        {"name": "Asramam Higher Secondary School Perumbavoor", "lat": 10.1130, "lon": 76.4740, "zone_id": "Z06", "capacity": 950},
        {"name": "NSS HSS Muvattupuzha", "lat": 9.9840, "lon": 76.5770, "zone_id": "Z07", "capacity": 750},
        {"name": "Nirmala College Muvattupuzha", "lat": 9.9760, "lon": 76.5840, "zone_id": "Z07", "capacity": 1500},
        {"name": "Mar Athanasius College Kothamangalam", "lat": 10.0570, "lon": 76.6260, "zone_id": "Z08", "capacity": 1700},
        {"name": "De Paul Institute of Science & Technology Angamaly", "lat": 10.1920, "lon": 76.3810, "zone_id": "Z09", "capacity": 1300},
        {"name": "Govt Sanskrit College Tripunithura", "lat": 9.9460, "lon": 76.3490, "zone_id": "Z10", "capacity": 900}
    ]
    pd.DataFrame(schools).to_csv(os.path.join(DATA_DIR, "schools.csv"), index=False)
    print("Saved hospitals and schools CSVs.")

def haversine_dist(lat1, lon1, lat2, lon2):
    R = 6371000 # meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def build_road_graph():
    print("Building road network graph of Ernakulam corridors...")
    G = nx.Graph()

    # Strategic junctions / nodes in Ernakulam district
    nodes = {
        "N_ALUVA_RSTN":   {"name": "Aluva Railway Station", "lat": 10.1080, "lon": 76.3530, "zone_id": "Z01"},
        "N_ALUVA_MANAP":  {"name": "Aluva Manappuram Ghat", "lat": 10.1140, "lon": 76.3480, "zone_id": "Z01"},
        "N_ALUVA_BANKJN": {"name": "Aluva Bank Junction", "lat": 10.1050, "lon": 76.3570, "zone_id": "Z01"},
        "N_PARAVUR_JN":   {"name": "North Paravur Town", "lat": 10.1450, "lon": 76.2300, "zone_id": "Z02"},
        "N_VARAPUZHA_BR": {"name": "Varapuzha Bridge", "lat": 10.0760, "lon": 76.2750, "zone_id": "Z02"},
        "N_EDAPPALLY_TOLL":{"name": "Edappally Toll / LuLu Junction", "lat": 10.0260, "lon": 76.3080, "zone_id": "Z03"},
        "N_KALOOR_STAD":  {"name": "Kaloor Stadium Junction", "lat": 9.9980, "lon": 76.2970, "zone_id": "Z03"},
        "N_EKM_SOUTH":    {"name": "Ernakulam South Railway Station", "lat": 9.9680, "lon": 76.2910, "zone_id": "Z03"},
        "N_MG_ROAD":      {"name": "MG Road / Shenoys Junction", "lat": 9.9780, "lon": 76.2820, "zone_id": "Z03"},
        "N_FORT_KOCHI":   {"name": "Fort Kochi Bus Stand", "lat": 9.9650, "lon": 76.2420, "zone_id": "Z04"},
        "N_MATTANCHERRY": {"name": "Mattancherry Market", "lat": 9.9570, "lon": 76.2550, "zone_id": "Z04"},
        "N_KALAMASSERY":  {"name": "Kalamassery Metro Junction", "lat": 10.0530, "lon": 76.3210, "zone_id": "Z05"},
        "N_CUSAT_JN":     {"name": "CUSAT University Gate", "lat": 10.0450, "lon": 76.3270, "zone_id": "Z05"},
        "N_CONTAINER_RD": {"name": "Container Terminal Highway", "lat": 10.0400, "lon": 76.2680, "zone_id": "Z05"},
        "N_PERUMBAVOOR":  {"name": "Perumbavoor Town Centre", "lat": 10.1110, "lon": 76.4780, "zone_id": "Z06"},
        "N_KALADY_BR":    {"name": "Kalady Bridge (Periyar)", "lat": 10.1650, "lon": 76.4380, "zone_id": "Z06"},
        "N_MUVATTUPUZHA": {"name": "Muvattupuzha Kacherithazham", "lat": 9.9830, "lon": 76.5800, "zone_id": "Z07"},
        "N_KOTHAMANGALAM":{"name": "Kothamangalam Town", "lat": 10.0620, "lon": 76.6320, "zone_id": "Z08"},
        "N_ANGAMALY_TOWN":{"name": "Angamaly KSRTC Centre", "lat": 10.1960, "lon": 76.3860, "zone_id": "Z09"},
        "N_CIAL_AIRPORT": {"name": "Cochin International Airport (CIAL)", "lat": 10.1520, "lon": 76.3920, "zone_id": "Z09"},
        "N_TRIPUNITHURA": {"name": "Tripunithura Statue Junction", "lat": 9.9480, "lon": 76.3480, "zone_id": "Z10"},
        "N_KAKKANAD_INFO": {"name": "Infopark Kakkanad Expressway", "lat": 10.0120, "lon": 76.3630, "zone_id": "Z03"}
    }

    for nid, d in nodes.items():
        G.add_node(nid, name=d["name"], lat=d["lat"], lon=d["lon"], zone_id=d["zone_id"])

    # Road links / edges connecting key junctions
    edges = [
        # Aluva local links
        ("N_ALUVA_MANAP", "N_ALUVA_RSTN", "Aluva Ghat Road", "Z01"),
        ("N_ALUVA_RSTN", "N_ALUVA_BANKJN", "Aluva Bank Road", "Z01"),
        ("N_ALUVA_BANKJN", "N_KALAMASSERY", "NH 544 Aluva-Kalamassery", "Z01"),

        # Kalamassery & City
        ("N_KALAMASSERY", "N_CUSAT_JN", "Kalamassery Highway", "Z05"),
        ("N_CUSAT_JN", "N_EDAPPALLY_TOLL", "NH 544 Edappally Stretch", "Z03"),
        ("N_EDAPPALLY_TOLL", "N_KALOOR_STAD", "Kaloor-Edappally Road", "Z03"),
        ("N_KALOOR_STAD", "N_MG_ROAD", "Banerji Road", "Z03"),
        ("N_MG_ROAD", "N_EKM_SOUTH", "MG Road Commercial Corridor", "Z03"),
        ("N_EKM_SOUTH", "N_TRIPUNITHURA", "SA Road - Pettah Link", "Z10"),

        # Bypass & Expressways
        ("N_EDAPPALLY_TOLL", "N_KAKKANAD_INFO", "Civil Station Kakkanad Road", "Z03"),
        ("N_KAKKANAD_INFO", "N_TRIPUNITHURA", "Seaport-Airport Road South", "Z10"),
        ("N_KALAMASSERY", "N_KAKKANAD_INFO", "Seaport-Airport Road North", "Z05"),
        ("N_CONTAINER_RD", "N_EDAPPALLY_TOLL", "Container Terminal Expressway", "Z05"),
        ("N_VARAPUZHA_BR", "N_CONTAINER_RD", "Varapuzha Container Link", "Z02"),

        # Paravur corridor
        ("N_ALUVA_MANAP", "N_PARAVUR_JN", "Aluva-Paravur Coastal Road", "Z01"),
        ("N_PARAVUR_JN", "N_VARAPUZHA_BR", "NH 66 Paravur-Varapuzha Link", "Z02"),

        # Fort Kochi & Mattancherry
        ("N_MG_ROAD", "N_FORT_KOCHI", "Willingdon Island - Thoppumpady Bridge", "Z04"),
        ("N_FORT_KOCHI", "N_MATTANCHERRY", "Bazar Road Historical Link", "Z04"),
        ("N_MATTANCHERRY", "N_TRIPUNITHURA", "Kundannoor - Maradu Link", "Z10"),

        # Angamaly & Airport
        ("N_ALUVA_RSTN", "N_CIAL_AIRPORT", "Airport Seaport VIP Expressway", "Z09"),
        ("N_CIAL_AIRPORT", "N_ANGAMALY_TOWN", "Airport North Approach Road", "Z09"),
        ("N_ALUVA_BANKJN", "N_ANGAMALY_TOWN", "NH 544 Aluva-Angamaly Main Arterial", "Z01"),

        # Perumbavoor & Kalady
        ("N_ALUVA_BANKJN", "N_PERUMBAVOOR", "AM Road (Aluva-Munnar Corridor)", "Z01"),
        ("N_ANGAMALY_TOWN", "N_KALADY_BR", "MC Road Angamaly-Kalady", "Z09"),
        ("N_KALADY_BR", "N_PERUMBAVOOR", "MC Road Kalady-Perumbavoor Bridge", "Z06"),

        # Muvattupuzha & Kothamangalam
        ("N_PERUMBAVOOR", "N_MUVATTUPUZHA", "MC Road Perumbavoor-Muvattupuzha", "Z06"),
        ("N_PERUMBAVOOR", "N_KOTHAMANGALAM", "Aluva-Munnar Road via Kothamangalam", "Z06"),
        ("N_MUVATTUPUZHA", "N_KOTHAMANGALAM", "Muvattupuzha-Kothamangalam Link Highway", "Z07"),
        ("N_TRIPUNITHURA", "N_MUVATTUPUZHA", "Kochi-Madurai NH 85 Extension", "Z07")
    ]

    edge_list = []
    for u, v, road_name, zone_id in edges:
        p1 = nodes[u]
        p2 = nodes[v]
        dist = haversine_dist(p1["lat"], p1["lon"], p2["lat"], p2["lon"])
        G.add_edge(u, v, name=road_name, length=round(dist, 1), zone_id=zone_id)
        edge_list.append({
            "u": u,
            "v": v,
            "name": road_name,
            "length": round(dist, 1),
            "zone_id": zone_id,
            "u_lat": p1["lat"],
            "u_lon": p1["lon"],
            "v_lat": p2["lat"],
            "v_lon": p2["lon"]
        })

    # Save NetworkX GraphML
    nx_path = os.path.join(DATA_DIR, "road_graph.graphml")
    nx.write_graphml(G, nx_path)
    print(f"Saved: {nx_path}")

    # Also save clean JSON for fast frontend and routing access
    graph_json = {
        "nodes": nodes,
        "edges": edge_list
    }
    json_path = os.path.join(DATA_DIR, "road_graph.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(graph_json, f, indent=2)
    print(f"Saved: {json_path}")

if __name__ == "__main__":
    build_features_and_geo()
    build_facilities()
    build_road_graph()
    print("Feature building and spatial datasets completed successfully.")
