"""
Impact Analysis Module (Module 4)
Computes threatened hospitals, impacted schools/camps, and affected road links based on risk thresholds.
"""
import pandas as pd

def compute_impact(zones_df: pd.DataFrame, hospitals_df: pd.DataFrame, schools_df: pd.DataFrame, edges_list: list):
    """
    Evaluates facility vulnerability in high and critical flood zones.
    """
    bad_zones = zones_df[zones_df["risk_class"].isin(["high", "critical"])]
    bad_zone_ids = set(bad_zones["zone_id"])

    # Filter hospitals in risky zones
    threatened_h = hospitals_df[hospitals_df["zone_id"].isin(bad_zone_ids)].copy()
    threatened_h_records = threatened_h.to_dict("records")

    # Filter schools / potential relief camps in risky zones
    impacted_s = schools_df[schools_df["zone_id"].isin(bad_zone_ids)].copy()
    impacted_s_records = impacted_s.to_dict("records")

    # Filter road segments in risky zones
    affected_roads = [e for e in edges_list if e.get("zone_id") in bad_zone_ids]

    critical_count = int((zones_df["risk_class"] == "critical").sum())
    high_count = int((zones_df["risk_class"] == "high").sum())
    medium_count = int((zones_df["risk_class"] == "medium").sum())
    low_count = int((zones_df["risk_class"] == "low").sum())

    total_beds_at_risk = int(threatened_h["beds"].sum()) if not threatened_h.empty else 0
    total_shelter_capacity = int(impacted_s["capacity"].sum()) if not impacted_s.empty else 0

    return {
        "counts": {
            "threatened_hospitals": len(threatened_h_records),
            "impacted_schools": len(impacted_s_records),
            "affected_roads": len(affected_roads),
            "critical_zones": critical_count,
            "high_zones": high_count,
            "medium_zones": medium_count,
            "low_zones": low_count,
            "total_beds_at_risk": total_beds_at_risk,
            "shelter_capacity": total_shelter_capacity
        },
        "threatened_hospitals": threatened_h_records,
        "impacted_schools": impacted_s_records,
        "affected_road_links": affected_roads
    }
