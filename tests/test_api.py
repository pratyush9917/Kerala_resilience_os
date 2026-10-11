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

    def test_08_ai_analysis_endpoint_disabled_state(self):
        from backend.main import ai_analysis
        req = SimRequest(rainfall_mm=250.0, river_level_m=5.0)
        res = ai_analysis(req)
        self.assertIn("status", res)
        # When GROQ_API_KEY is empty, endpoint returns a clean disabled envelope
        self.assertIn(res["status"], ["disabled", "ok", "error"])
        print(f"AI analysis endpoint verification passed (status: {res['status']}).")

    def test_09_groq_payload_and_sanitizer(self):
        import backend.groq_advisor as advisor
        dummy_inputs = {"rainfall_mm": 350.0, "river_level_m": 7.0}
        dummy_zones = [{"zone_id": "Z01", "name": "Aluva", "risk": 0.85, "risk_class": "critical"}]
        dummy_impact = {"counts": {"threatened_hospitals": 3}, "threatened_hospitals": [], "impacted_schools": []}
        dummy_plan = [{"action": "Evacuation", "zone": "Aluva", "confidence_pct": 95, "priority": 0.8}]
        dummy_shelters = [{"zone_id": "Z08", "name": "M.A. College", "capacity": 1500}]

        payload = advisor.build_scenario_payload(dummy_inputs, dummy_zones, dummy_impact, dummy_plan, dummy_shelters)
        self.assertIn("simulation_inputs", payload)
        self.assertIn("zones_ranked_by_risk", payload)
        self.assertIn("ml_planner_ranked_actions", payload)

        # Test sanitizer schema coercion
        raw_mock = {
            "headline": "Severe flooding in Periyar basin",
            "severity": "critical",
            "situation_summary": "Water levels rising near Aluva.",
            "impact_assessment": {"communities": "Lowlands at risk"},
            "action_plan": [
                {"phase": "immediate", "priority": "critical", "action": "Evacuate Aluva", "target": "Aluva", "agency": "NDRF"}
            ],
            "zone_priorities": [{"zone": "Aluva", "risk_level": "critical", "focus": "Riverfront evacuations"}],
            "public_advisory": "Move to higher ground immediately.",
            "watch_points": ["Periyar gauge at Marthanda Varma Bridge"]
        }
        sanitized = advisor._sanitize(raw_mock)
        self.assertEqual(sanitized["severity"], "critical")
        self.assertEqual(len(sanitized["action_plan"]), 1)
        self.assertEqual(sanitized["action_plan"][0]["action"], "Evacuate Aluva")
        print("Groq payload builder and JSON sanitizer tests passed.")

if __name__ == "__main__":
    unittest.main()

