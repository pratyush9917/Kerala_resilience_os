"""Groq-backed advisor for simulation briefings."""
import json
import re
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from backend.config import (
    GROQ_MODEL,
    GROQ_TEMPERATURE,
    GROQ_TIMEOUT_S,
    get_groq_api_key,
)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = get_groq_api_key()
SEVERITIES = ("low", "moderate", "high", "critical", "catastrophic")
PHASES = ("immediate", "short_term", "next_24h")
PRIORITIES = ("critical", "high", "medium")


def is_configured() -> bool:
    return bool(GROQ_API_KEY)


def build_scenario_payload(inputs, zones, impact, plan, all_shelters):
    """Build a compact, server-generated payload for the advisor."""
    sorted_zones = sorted(zones, key=lambda row: -float(row.get("risk", 0)))
    name_by_id = {row.get("zone_id"): row.get("name") for row in zones}
    class_by_id = {row.get("zone_id"): row.get("risk_class") for row in zones}
    return {
        "simulation_inputs": {
            "rainfall_mm_24h": inputs.get("rainfall_mm"),
            "periyar_river_level_m": inputs.get("river_level_m"),
        },
        "district_summary": impact.get("counts", {}),
        "zones_ranked_by_risk": [
            {
                "zone": row.get("name"),
                "zone_id": row.get("zone_id"),
                "risk_score": row.get("risk"),
                "risk_class": row.get("risk_class"),
                "elevation_m": row.get("elevation_m"),
                "river_proximity": row.get("river_prox"),
                "historical_2018_severity": row.get("hist_risk"),
                "road_vulnerability": row.get("road_vuln"),
                "hospitals": row.get("n_hospitals"),
                "schools_or_camps": row.get("n_schools"),
                "risk_factor_contributions": row.get("factors"),
            }
            for row in sorted_zones
        ],
        "threatened_hospitals": [
            {"name": item.get("name"), "zone": name_by_id.get(item.get("zone_id")), "beds": item.get("beds")}
            for item in impact.get("threatened_hospitals", [])
        ],
        "impacted_shelters_in_flood_zones": [
            {"name": item.get("name"), "zone": name_by_id.get(item.get("zone_id")), "capacity": item.get("capacity")}
            for item in impact.get("impacted_schools", [])
        ],
        "safe_zone_shelters_available": [
            {"name": item.get("name"), "zone": name_by_id.get(item.get("zone_id")), "capacity": item.get("capacity")}
            for item in sorted(
                (item for item in all_shelters if class_by_id.get(item.get("zone_id")) in ("low", "medium")),
                key=lambda item: -int(item.get("capacity", 0)),
            )[:10]
        ],
        "ml_planner_ranked_actions": [
            {
                "action": item.get("action"),
                "zone": item.get("zone"),
                "confidence_pct": item.get("confidence_pct"),
                "priority_score": item.get("priority"),
                "target_sites": item.get("places"),
            }
            for item in plan[:12]
        ],
    }


def generate_briefing(payload):
    """Return a validated Groq briefing without raising into the API."""
    if not GROQ_API_KEY:
        return {
            "status": "disabled",
            "message": "Groq is not configured yet. Add your GROQ_API_KEY to the .env file to enable live AI briefings.",
        }
    body = {
        "model": GROQ_MODEL,
        "temperature": GROQ_TEMPERATURE,
        "max_tokens": 2200,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "Return one concise JSON flood response briefing."},
            {"role": "user", "content": "Simulation output (JSON):\n" + json.dumps(payload, default=_json_default)},
        ],
    }
    started = time.time()
    try:
        raw = _post(body, api_key=GROQ_API_KEY)
        content = raw["choices"][0]["message"]["content"]
        briefing = _sanitize(_extract_json(content))
    except HTTPError as exc:
        return {"status": "error", "message": _http_error_message(exc)}
    except (URLError, TimeoutError, OSError) as exc:
        return {"status": "error", "message": f"Could not reach Groq ({exc.__class__.__name__}). Check the network connection."}
    except (KeyError, IndexError, ValueError, TypeError):
        return {"status": "error", "message": "Groq returned a response that could not be read. Try running the simulation again."}
    return {
        "status": "ok",
        "model": raw.get("model", GROQ_MODEL),
        "latency_ms": int((time.time() - started) * 1000),
        "briefing": briefing,
    }


def _post(body, api_key):
    request = Request(
        GROQ_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "KeralaResilienceOS/1.0",
        },
        method="POST",
    )
    with urlopen(request, timeout=GROQ_TIMEOUT_S) as response:
        return json.loads(response.read().decode("utf-8"))


def _http_error_message(exc):
    if exc.code == 401:
        return "Groq rejected the API key (401). Check GROQ_API_KEY in .env."
    if exc.code == 429:
        return "Groq rate limit reached (429). Wait a few seconds and run the simulation again."
    if exc.code in (400, 404):
        return f"Groq rejected the request ({exc.code}). Check that GROQ_MODEL in .env is a valid model name."
    return f"Groq returned an error ({exc.code})."


def _extract_json(text):
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", (text or "").strip())
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("No JSON object in response")
        value = json.loads(cleaned[start:end + 1])
    if not isinstance(value, dict):
        raise ValueError("Response is not an object")
    return value


def _text(value, limit=500):
    return str(value or "").strip()[:limit]


def _sanitize(raw):
    impact = raw.get("impact_assessment")
    impact = impact if isinstance(impact, dict) else {}
    severity = str(raw.get("severity", "")).lower()
    result = {
        "headline": _text(raw.get("headline"), 120),
        "severity": severity if severity in SEVERITIES else "moderate",
        "situation_summary": _text(raw.get("situation_summary")),
        "impact_assessment": {key: _text(impact.get(key)) for key in ("communities", "healthcare", "shelters", "transport", "outlook")},
        "action_plan": [],
        "zone_priorities": [],
        "public_advisory": _text(raw.get("public_advisory")),
        "watch_points": [_text(item, 200) for item in raw.get("watch_points", []) if item][:5] if isinstance(raw.get("watch_points"), list) else [],
        "ml_plan_review": _text(raw.get("ml_plan_review")),
    }
    for item in raw.get("action_plan", []) if isinstance(raw.get("action_plan"), list) else []:
        if not isinstance(item, dict) or not _text(item.get("action")):
            continue
        phase = str(item.get("phase", "")).lower()
        priority = str(item.get("priority", "")).lower()
        result["action_plan"].append({
            "phase": phase if phase in PHASES else "immediate",
            "priority": priority if priority in PRIORITIES else "medium",
            "action": _text(item.get("action"), 300),
            "target": _text(item.get("target"), 200),
            "agency": _text(item.get("agency"), 120),
            "rationale": _text(item.get("rationale"), 300),
        })
        if len(result["action_plan"]) == 10:
            break
    return result


def _json_default(obj):
    return obj.item() if hasattr(obj, "item") else str(obj)
