"""
Automated Test Suite for Kerala Resilience OS
Validates Testing Checklist (Section 16 of Project Documentation)
"""
import sys
import os
import unittest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import simulate, get_route, get_zones, health_check, SimRequest
from backend.risk_engine import score_zones
import backend.routing as routing

class TestKeralaResilienceOS(unittest.TestCase):

    def test_01_health_endpoint(self):
        data = health_check()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["district"], "Ernakulam, Kerala")
        self.assertEqual(data["zones_count"], 10)
        self.assertEqual(len(data["ai_models_loaded"]), 3)

    def test_02_zones_endpoint(self):
        data = get_zones()
        self.assertIn("geojson", data)
        self.assertIn("hospitals", data)
        self.assertIn("schools", data)
        self.assertIn("road_network", data)
        self.assertEqual(len(data["zones"]), 10)

    def test_03_simulate_baseline_dry_day(self):
        # 0 mm rain, 0 m river -> mostly low risk
        req = SimRequest(rainfall_mm=0.0, river_level_m=0.0)
        data = simulate(req)
        zones = data["zones"]
        self.assertTrue(all(z["risk"] < 0.60 for z in zones))
        critical_count = sum(1 for z in zones if z["risk_class"] == "critical")
        self.assertEqual(critical_count, 0)
        print("Dry day simulation passed (0 critical zones).")

    def test_04_simulate_2018_extreme_flood(self):
        # 750 mm rain, 12 m river -> Aluva & Paravur should become high or critical
        req = SimRequest(rainfall_mm=750.0, river_level_m=12.0)
        data = simulate(req)
        zones = data["zones"]
        aluva = next(z for z in zones if z["zone_id"] == "Z01")
        paravur = next(z for z in zones if z["zone_id"] == "Z02")
        self.assertIn(aluva["risk_class"], ["high", "critical"])
        self.assertIn(paravur["risk_class"], ["high", "critical"])
        self.assertGreater(data["impact"]["counts"]["threatened_hospitals"], 0)
        self.assertGreater(len(data["plan"]), 0)
        print(f"2018 extreme flood simulation passed (Aluva: {aluva['risk_class']}, Paravur: {paravur['risk_class']}).")

    def test_05_monotonicity_check(self):
        # Increasing rainfall must never reduce any zone's risk
        zones_df = pd.read_csv("data/processed/zones_features.csv")
        r1 = score_zones(zones_df, 100.0, 3.0)["risk"].values
        r2 = score_zones(zones_df, 300.0, 3.0)["risk"].values
        r3 = score_zones(zones_df, 600.0, 3.0)["risk"].values
        for i in range(len(r1)):
            self.assertGreaterEqual(r2[i] + 0.01, r1[i])
            self.assertGreaterEqual(r3[i] + 0.01, r2[i])
        print("Monotonicity verification passed.")

    def test_06_routing_under_moderate_conditions(self):
        # Simulate moderate monsoon (roads open)
        simulate(SimRequest(rainfall_mm=120.0, river_level_m=3.5))
        # Route from Kakkanad Infopark to Ernakulam South
        data = get_route(from_lat=10.012, from_lon=76.363, to_lat=9.968, to_lon=76.291)
        self.assertIn("safest", data)
        self.assertIn("shortest", data)
        self.assertEqual(data["safest"]["status"], "success")
        self.assertEqual(data["shortest"]["status"], "success")
        self.assertGreater(len(data["safest"]["coordinates"]), 1)
        print(f"Routing passed: Shortest {data['shortest']['distance_km']}km, Safest {data['safest']['distance_km']}km.")

    def test_07_routing_same_origin_destination(self):
        data = get_route(from_lat=10.108, from_lon=76.353, to_lat=10.108, to_lon=76.353)
        self.assertEqual(data["safest"]["status"], "success")
        self.assertEqual(data["safest"]["distance_km"], 0.0)
        print("Identical origin-dest routing handled gracefully.")

if __name__ == "__main__":
    unittest.main()
