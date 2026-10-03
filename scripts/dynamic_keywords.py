"""
Adaptive Dynamic Keyword Evolution (ADKE) Engine for Global AI Incident Monitor.
Learns novel entities, model names, and threat vectors from confirmed AI incidents,
maintains a weighted dynamic keyword pool with daily decay, TTL, and anti-drift guardrails.
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional

DYNAMIC_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "dynamic_keywords.json")

# Generic stop words and financial noise terms to prevent semantic drift
ANTI_DRIFT_STOPWORDS = {
    "the", "and", "for", "that", "with", "from", "this", "have", "were", "been", "about",
    "after", "used", "using", "over", "into", "incidents", "incident", "report", "news",
    "says", "said", "will", "also", "their", "which", "other", "more", "some", "such",
    "when", "what", "where", "how", "than", "them", "these", "user", "users", "company",
    "companies", "first", "resulting", "tools", "tool", "agent", "agents", "system", "systems", "model",
    "models", "artificial", "intelligence", "data", "ai", "tech", "technology", "update",
    "updates", "ceo", "chief", "executive", "officer", "revenue", "profit", "quarter", "quarterly", "q1", "q2", "q3", "q4",
    "stock", "shares", "valuation", "investor", "investors", "earnings", "growth", "sales", "market",
    "business", "conference", "statement", "announced", "release", "releases", "future", "world", "today", "global", "people", "year", "years"
}

LANE_SYSTEM_MAP = {
    "frontier_llms_leaks": ["general_purpose_model", "dual_use_security"],
    "autonomous_agents_cyber": ["autonomous_agent", "critical_infrastructure_component"],
    "biometrics_police_surveillance": ["biometric_identification"],
    "autonomous_mobility_robotics": ["autonomous_mobility"],
    "multimodal_media_deepfakes": ["generative_content"],
    "social_chatbots_harm_governance": ["high_risk_regulated", "unclassified"]
}

def load_dynamic_keywords() -> Dict[str, Any]:
    """Loads dynamic keyword pool from config/dynamic_keywords.json."""
    if os.path.exists(DYNAMIC_CONFIG_PATH):
        try:
            with open(DYNAMIC_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load dynamic_keywords.json: {e}")
    
    return {
        "_meta": {
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "decay_rate_daily": 0.05,
            "min_weight_threshold": 0.20,
            "max_ttl_days": 21,
            "max_active_per_lane": 4
        },
        "lanes": {
            "frontier_llms_leaks": [],
            "autonomous_agents_cyber": [],
            "biometrics_police_surveillance": [],
            "autonomous_mobility_robotics": [],
            "multimodal_media_deepfakes": [],
            "social_chatbots_harm_governance": []
        }
    }

def save_dynamic_keywords(pool: Dict[str, Any]) -> None:
    """Saves updated dynamic keyword pool to config/dynamic_keywords.json."""
    pool["_meta"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    try:
        os.makedirs(os.path.dirname(DYNAMIC_CONFIG_PATH), exist_ok=True)
        with open(DYNAMIC_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(pool, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ERROR] Failed to save dynamic_keywords.json: {e}")

def clean_candidate_phrase(term: str) -> str:
    """
    Cleans raw candidate phrase:
    - Normalizes whitespace and removes punctuation.
    - Strips leading and trailing stopwords (e.g. 'and API credential' -> 'API credential').
    """
    if not term or not isinstance(term, str):
        return ""
    
    cleaned = re.sub(r'[^a-zA-Z0-9\s-]', '', term.strip())
    words = cleaned.split()
    
    # Strip leading stopwords
    while words and words[0].lower() in ANTI_DRIFT_STOPWORDS:
        words.pop(0)
    
    # Strip trailing stopwords
    while words and words[-1].lower() in ANTI_DRIFT_STOPWORDS:
        words.pop()
        
    return " ".join(words)

def anti_drift_validate_term(term: str) -> bool:
    """
    Strict Anti-Drift Guardrail:
    - Must be between 3 and 35 characters.
    - Max 3 words.
    - Rejects terms consisting purely of stopwords or generic business/financial buzzwords.
    - Rejects pure numbers, URLs, or punctuation-heavy strings.
    """
    if not term or not isinstance(term, str):
        return False
    
    cleaned = clean_candidate_phrase(term)
    if len(cleaned) < 3 or len(cleaned) > 35:
        return False
    
    words = cleaned.lower().split()
    if len(words) > 3 or len(words) == 0:
        return False
    
    # Reject if all words are generic stopwords
    meaningful_words = [w for w in words if w not in ANTI_DRIFT_STOPWORDS and not w.isdigit()]
    if not meaningful_words:
        return False
    
    return True

def map_incident_to_lane(incident: Dict[str, Any]) -> str:
    """Determines the most appropriate harvesting lane for an incident."""
    sys_class = incident.get("system_classification", "")
    primary_purpose = incident.get("primary_purpose", "")
    harm_type = incident.get("harm_type", "")
    title_summary = (incident.get("title", "") + " " + incident.get("summary", "")).lower()

    if sys_class == "autonomous_agent" or "agent" in title_summary or "crawler" in title_summary:
        return "autonomous_agents_cyber"
    if sys_class == "biometric_identification" or "facial recognition" in title_summary or "flock" in title_summary:
        return "biometrics_police_surveillance"
    if primary_purpose == "autonomous_mobility" or "waymo" in title_summary or "tesla" in title_summary or "crash" in title_summary:
        return "autonomous_mobility_robotics"
    if "deepfake" in title_summary or "voice clone" in title_summary or harm_type in ["copyright_ip", "misinformation"]:
        return "multimodal_media_deepfakes"
    if harm_type in ["psychological_harm", "physical_safety"] or "character" in title_summary or "child" in title_summary:
        return "social_chatbots_harm_governance"
    
    return "frontier_llms_leaks"

def extract_emerging_entities_from_incident(incident: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extracts candidate dynamic terms (models, products, organizations, threat mechanisms)
    from a confirmed incident.
    """
    candidates = []
    lane = map_incident_to_lane(incident)
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 1. Extract affected parties (specific tool/model/organization names)
    for party in (incident.get("affected_parties") or []):
        cleaned_party = clean_candidate_phrase(party)
        if anti_drift_validate_term(cleaned_party):
            candidates.append({
                "term": cleaned_party,
                "type": "subject",
                "lane": lane,
                "first_seen": today_str,
                "last_hit": today_str
            })

    # 2. Extract key phrases from failure_mode & root_cause_subtype
    failure_mode = incident.get("failure_mode", "")
    subtype = incident.get("root_cause_subtype", "")
    for text_source in [failure_mode, subtype]:
        if text_source:
            # Extract 2-3 word technical compound phrases
            matches = re.findall(r'\b[A-Za-z0-9-]{3,}(?:\s+[A-Za-z0-9-]{3,}){1,2}\b', text_source)
            for m in matches:
                cleaned_m = clean_candidate_phrase(m)
                if anti_drift_validate_term(cleaned_m):
                    candidates.append({
                        "term": cleaned_m,
                        "type": "incident",
                        "lane": lane,
                        "first_seen": today_str,
                        "last_hit": today_str
                    })

    return candidates

def apply_keyword_decay_and_cleanup(pool: Dict[str, Any]) -> Tuple[int, int]:
    """
    Applies daily 5% decay to inactive dynamic keywords and purges terms that:
    1. Drop below weight threshold (< 0.20)
    2. Exceed maximum TTL (21 days) without any recent hit
    Returns (decayed_count, purged_count).
    """
    decay_rate = pool.get("_meta", {}).get("decay_rate_daily", 0.05)
    min_weight = pool.get("_meta", {}).get("min_weight_threshold", 0.20)
    max_ttl = pool.get("_meta", {}).get("max_ttl_days", 21)
    today = datetime.now()

    decayed_count = 0
    purged_count = 0

    lanes = pool.get("lanes", {})
    for lane_key, term_list in lanes.items():
        surviving_terms = []
        for term_obj in term_list:
            last_hit_str = term_obj.get("last_hit", term_obj.get("first_seen", today.strftime("%Y-%m-%d")))
            try:
                last_hit_date = datetime.strptime(last_hit_str, "%Y-%m-%d")
            except Exception:
                last_hit_date = today

            days_since_hit = (today - last_hit_date).days
            
            # Apply decay if untouched today
            if days_since_hit > 0:
                decay_factor = (1.0 - decay_rate) ** days_since_hit
                term_obj["weight"] = round(term_obj.get("weight", 1.0) * decay_factor, 3)
                decayed_count += 1

            # Check survival criteria
            if term_obj.get("weight", 0) >= min_weight and days_since_hit <= max_ttl:
                surviving_terms.append(term_obj)
            else:
                purged_count += 1

        # Keep top terms sorted by weight
        surviving_terms.sort(key=lambda x: (x.get("weight", 0), x.get("hit_count", 0)), reverse=True)
        max_active = pool.get("_meta", {}).get("max_active_per_lane", 4)
        lanes[lane_key] = surviving_terms[:max_active * 2] # Keep buffer

    return decayed_count, purged_count

def learn_and_update_keywords(confirmed_incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Post-Ingestion Adaptive Learning Loop:
    1. Extracts emerging entities & attack vectors from day's confirmed incidents.
    2. Applies reinforcement (+weight, +hit_count, reset TTL) or registers new candidate terms.
    3. Runs daily decay and cleanup on older terms.
    4. Persists updated dynamic keyword pool to config/dynamic_keywords.json.
    """
    pool = load_dynamic_keywords()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    newly_added = 0
    reinforced = 0

    # 1. Extract emerging terms
    for inc in confirmed_incidents:
        candidates = extract_emerging_entities_from_incident(inc)
        for cand in candidates:
            lane = cand["lane"]
            term_clean = cand["term"].lower()
            lane_terms = pool["lanes"].setdefault(lane, [])

            # Check if term already exists in lane
            existing = next((t for t in lane_terms if t["term"].lower() == term_clean), None)
            if existing:
                existing["hit_count"] = existing.get("hit_count", 1) + 1
                existing["weight"] = min(1.0, existing.get("weight", 0.8) + 0.15)
                existing["last_hit"] = today_str
                reinforced += 1
            else:
                lane_terms.append({
                    "term": cand["term"],
                    "type": cand["type"],
                    "weight": 0.85,
                    "hit_count": 1,
                    "first_seen": today_str,
                    "last_hit": today_str
                })
                newly_added += 1

    # 2. Decay and cleanup
    decayed, purged = apply_keyword_decay_and_cleanup(pool)

    # 3. Save pool
    save_dynamic_keywords(pool)

    telemetry = {
        "newly_added": newly_added,
        "reinforced": reinforced,
        "decayed": decayed,
        "purged": purged,
        "total_active": sum(len(terms) for terms in pool.get("lanes", {}).values())
    }
    print(f"\n[ADAPTIVE KEYWORD EVOLUTION] Learned: +{newly_added} new | Reinforced: {reinforced} | Decayed: {decayed} | Purged: {purged} | Active Pool: {telemetry['total_active']} terms.")
    return telemetry

def get_top_dynamic_keywords_for_lane(lane_key: str, max_items: int = 4) -> Dict[str, List[str]]:
    """
    Returns the top active dynamic subjects and incident terms for a specific lane.
    """
    pool = load_dynamic_keywords()
    lane_terms = pool.get("lanes", {}).get(lane_key, [])
    
    # Sort by weight descending
    sorted_terms = sorted(lane_terms, key=lambda x: (x.get("weight", 0), x.get("hit_count", 0)), reverse=True)
    
    top_subjects = [t["term"] for t in sorted_terms if t.get("type") == "subject"][:max_items]
    top_incidents = [t["term"] for t in sorted_terms if t.get("type") == "incident"][:max_items]
    
    return {
        "subjects": top_subjects,
        "incidents": top_incidents
    }
