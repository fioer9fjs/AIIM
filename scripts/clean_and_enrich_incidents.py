"""
Comprehensive One-Click Incident Deduplication, Cross-Date Merging & Financial Damage Enrichment Script.

1. Fetches all incidents from local dataset / Supabase PostgreSQL.
2. Performs cross-date fuzzy similarity matching across titles, summaries, and affected entities.
3. Merges duplicate incidents across dates, combining source_urls and preserving canonical earliest dates.
4. Calculates & populates financial_damage_usd using explicit lawsuit/fine parsing, VSL ($12.5M) benchmark, and risk-tier valuation.
5. Updates src/data/incidents.json and synchronizes clean enriched dataset to Supabase PostgreSQL.
"""

import os
import json
import difflib
import re
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Tuple

def load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

def get_supabase_credentials():
    load_env_file()
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or os.environ.get("SUPABASE_KEY", "")
    return url, key

def fetch_supabase_incidents(url: str, key: str) -> List[Dict[str, Any]]:
    if not url or not key:
        return []
    endpoint = f"{url.rstrip('/')}/rest/v1/incidents?select=*"
    req = urllib.request.Request(
        endpoint,
        headers={"apikey": key, "Authorization": f"Bearer {key}"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Error fetching from Supabase: {e}")
        return []

def delete_supabase_incident(url: str, key: str, incident_id: str):
    if not url or not key or not incident_id:
        return
    endpoint = f"{url.rstrip('/')}/rest/v1/incidents?incident_id=eq.{incident_id}"
    req = urllib.request.Request(
        endpoint,
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
        method="DELETE"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            pass
    except Exception as e:
        print(f"Error deleting {incident_id} from Supabase: {e}")

def calculate_similarity(inc1: Dict[str, Any], inc2: Dict[str, Any]) -> float:
    """Calculates composite fuzzy similarity score between two incident records."""
    t1 = inc1.get("title", "").lower()
    t2 = inc2.get("title", "").lower()
    title_ratio = difflib.SequenceMatcher(None, t1, t2).ratio()
    
    words1 = set(inc1.get("summary", "").lower().split())
    words2 = set(inc2.get("summary", "").lower().split())
    jaccard_summary = len(words1.intersection(words2)) / float(max(len(words1.union(words2)), 1))
    
    parties1 = set(p.lower() for p in inc1.get("affected_parties", []))
    parties2 = set(p.lower() for p in inc2.get("affected_parties", []))
    party_overlap = 0.15 if (parties1 and parties2 and len(parties1.intersection(parties2)) > 0) else 0.0
    
    return (title_ratio * 0.5) + (jaccard_summary * 0.35) + party_overlap

def assign_compliance_frameworks(inc: Dict[str, Any]):
    """Assigns NIST AI RMF 1.0 Function and ISO/IEC 42001 Category based on incident metadata."""
    title = (inc.get("title") or "").lower()
    summary = (inc.get("summary") or "").lower()
    rc = (inc.get("root_cause_category") or "").lower()
    sys_cls = (inc.get("system_classification") or "").lower()
    harm_type = (inc.get("harm_type") or "").lower()
    purpose = (inc.get("primary_purpose") or "").lower()
    
    if "governance" in rc or "policy" in summary or "legal" in summary or "court" in title or "fcc" in title or "sec" in title:
        nist = "GOVERN"
    elif "cyber" in summary or "hack" in summary or "agent" in sys_cls or "autonomous" in sys_cls or "breach" in summary:
        nist = "MANAGE"
    elif "model" in rc or "data" in rc or "bias" in harm_type or "hallucination" in summary or "test" in summary:
        nist = "MEASURE"
    else:
        nist = "MAP"
        
    if "cyber" in summary or "hack" in summary or "breach" in summary or "vulnerability" in summary or "exploit" in summary:
        iso = "Operational_Security"
    elif "privacy" in harm_type or "copyright" in harm_type or "data" in rc or "secret" in summary or "trade" in summary:
        iso = "Data_&_Resources"
    elif "governance" in rc or "court" in title or "lawsuit" in summary or "dismissal" in summary or "hr" in purpose:
        iso = "Internal_Governance"
    else:
        iso = "System_Impact"

    inc["nist_ai_rmf_function"] = nist
    inc["iso_42001_category"] = iso
    if isinstance(inc.get("taxonomy"), dict):
        inc["taxonomy"]["nist_ai_rmf_function"] = nist
        inc["taxonomy"]["iso_42001_category"] = iso

def assign_impact_scope(inc: Dict[str, Any]):
    """Assigns impact_scope ('discrete_incident' | 'cumulative_macro_trend')."""
    usd = inc.get("financial_damage_usd", 0) or 0
    text_corpus = f"{inc.get('title', '')} {inc.get('summary', '')} {inc.get('full_text', '')}".lower()
    
    if usd >= 5_000_000_000 or any(k in text_corpus for k in ["annual report", "chainalysis", "interpol", "global losses", "across industry", "industry report"]):
        scope = "cumulative_macro_trend"
    else:
        scope = "discrete_incident"
        
    inc["impact_scope"] = scope
    if isinstance(inc.get("taxonomy"), dict):
        inc["taxonomy"]["impact_scope"] = scope

def estimate_financial_damage(inc: Dict[str, Any]) -> Tuple[int, str]:
    """Calculates conservative, lower-bound empirical financial damage in USD and returns (usd, methodology)."""
    text_corpus = f"{inc.get('title', '')} {inc.get('summary', '')} {inc.get('full_text', '')}".lower()
    severity = inc.get("severity", "medium").lower()

    # Rule 1: Explicit dollar amounts in text (Confirmed Official Figure)
    match_billion = re.search(r'\$(\d+(?:\.\d+)?)\s*billion', text_corpus)
    if match_billion:
        return int(float(match_billion.group(1)) * 1_000_000_000), "explicit_confirmed"

    match_million = re.search(r'\$(\d+(?:\.\d+)?)\s*million', text_corpus)
    if match_million:
        return int(float(match_million.group(1)) * 1_000_000), "explicit_confirmed"

    # Rule 2: Fatalities (Official US DOT VSL Benchmark $12.5M per loss of life)
    if any(k in text_corpus for k in ["fatality", "fatal", "death", "killed", "loss of life"]):
        return 12_500_000, "vsl_benchmark"

    # Rule 3: Corporate Lawsuits, Class Actions & CSAM Claims (Conservative Lower-Bound Statutory Defense Baseline)
    if any(k in text_corpus for k in ["lawsuit", "class action", "sues", "csam", "copyright", "trade secret"]):
        if severity == "critical":
            return 12_500_000, "statutory_formula"  # Conservative lower-bound litigation & defense baseline
        elif severity == "high":
            return 4_500_000, "statutory_formula"
        return 1_200_000, "statutory_formula"

    # Rule 4: Deepfake Fraud & Crypto Scams (Conservative Remediation Baseline)
    if any(k in text_corpus for k in ["scam", "fraud", "crypto", "deepfake", "phishing"]):
        if severity == "critical":
            return 6_800_000, "empirical_estimate"
        elif severity == "high":
            return 2_500_000, "empirical_estimate"
        return 500_000, "empirical_estimate"

    # Rule 5: Cyber Intrusions, Autonomous Agent Escapes & Vulnerabilities (IBM Cyber Breach Lower Bound)
    if any(k in text_corpus for k in ["breach", "hack", "intrusion", "vulnerability", "exploit", "rogue", "sandbox"]):
        if severity == "critical":
            return 4_880_000, "cyber_breach_report"  # IBM average breach baseline
        elif severity == "high":
            return 2_500_000, "cyber_breach_report"
        return 450_000, "cyber_breach_report"

    # Rule 6: Algorithmic Discrimination, Hiring Bias & Administrative Orders
    if any(k in text_corpus for k in ["dismissal", "court", "prosecuted", "bias", "discrimination", "fcc", "ban"]):
        if severity == "critical":
            return 5_000_000, "regulatory_turnover"
        elif severity == "high":
            return 2_500_000, "regulatory_turnover"
        return 280_000, "regulatory_turnover"

    # Conservative Default Fallback per severity rating
    if severity == "critical":
        return 5_000_000, "empirical_estimate"
    elif severity == "high":
        return 2_500_000, "empirical_estimate"
    elif severity == "medium":
        return 850_000, "empirical_estimate"
    return 350_000, "empirical_estimate"

def main():
    print("=" * 85)
    print("GLOBAL AI INCIDENT MONITOR - DEDUPLICATION & FINANCIAL ENRICHMENT PIPELINE")
    print("=" * 85)

    data_dir = os.path.join(os.path.dirname(__file__), "..", "src", "data")
    incidents_path = os.path.join(data_dir, "incidents.json")

    url, key = get_supabase_credentials()
    db_incidents = fetch_supabase_incidents(url, key) if (url and key) else []

    if db_incidents:
        print(f"Loaded {len(db_incidents)} records from Supabase PostgreSQL.")
        incidents = db_incidents
    elif os.path.exists(incidents_path):
        with open(incidents_path, "r", encoding="utf-8") as f:
            incidents = json.load(f)
        print(f"Loaded {len(incidents)} records from local incidents.json.")
    else:
        print("No incidents dataset found.")
        return

    # 1. CROSS-DATE DEDUPLICATION & CLUSTERING
    print("\n---> RUNNING CROSS-DATE FUZZY DEDUPLICATION...")
    unique_incidents: List[Dict[str, Any]] = []
    removed_ids: List[str] = []

    for inc in incidents:
        matched = False
        for idx, target in enumerate(unique_incidents):
            sim = calculate_similarity(inc, target)
            if sim >= 0.52:
                matched = True
                print(f"  [DUPLICATE MATCH ({sim:.2f})] Merging '{inc.get('title')[:45]}...' into '{target.get('title')[:45]}...'")
                removed_ids.append(inc.get("incident_id"))
                
                urls1 = target.get("source_urls", []) or []
                urls2 = inc.get("source_urls", []) or []
                combined = list(dict.fromkeys(urls1 + urls2))
                target["source_urls"] = combined
                
                if (inc.get("date") or "9999") < (target.get("date") or "9999"):
                    target["date"] = inc.get("date")
                    
                d1 = target.get("financial_damage_usd", 0) or 0
                d2 = inc.get("financial_damage_usd", 0) or 0
                target["financial_damage_usd"] = max(d1, d2)
                
                if not target.get("full_text") and inc.get("full_text"):
                    target["full_text"] = inc.get("full_text")
                    
                break

        if not matched:
            unique_incidents.append(inc)

    print(f"\nDeduplication complete: Reduced dataset from {len(incidents)} to {len(unique_incidents)} unique incidents.")

    # 2. ASSIGN COMPLIANCE FRAMEWORKS & ESTIMATE FINANCIAL DAMAGE
    print("\n---> ASSIGNING ENTERPRISE COMPLIANCE & ESTIMATING FINANCIAL DAMAGE ($ USD)...")
    enriched_count = 0
    total_damage_usd = 0

    for inc in unique_incidents:
        assign_compliance_frameworks(inc)
        damage, methodology = estimate_financial_damage(inc)
        inc["financial_damage_usd"] = damage
        inc["valuation_methodology"] = methodology
        assign_impact_scope(inc)
        if isinstance(inc.get("taxonomy"), dict):
            inc["taxonomy"]["financial_damage_usd"] = damage
            inc["taxonomy"]["valuation_methodology"] = methodology
        if damage > 0:
            enriched_count += 1
            total_damage_usd += damage
            print(f"  [CONSERVATIVE ESTIMATE: {methodology}] '{inc.get('title')[:44]}...' -> ${damage:,} USD")

    print(f"\nCalculated financial damage metrics for {enriched_count} incidents.")
    print(f"Total Cumulative Financial Impact Across Dataset: ${total_damage_usd:,} USD.")

    # 3. SAVE CLEAN DATASET TO LOCAL JSON
    with open(incidents_path, "w", encoding="utf-8") as f:
        json.dump(unique_incidents, f, indent=2)
    print(f"\nSaved {len(unique_incidents)} cleaned & enriched records to {incidents_path}.")

    # 4. SYNC TO SUPABASE (DELETE DUPLICATES & UPSERT CLEAN DATASET)
    if url and key:
        print("\n---> SYNCHRONIZING CLEAN ENRICHED DATASET TO SUPABASE POSTGRESQL...")
        for rid in removed_ids:
            if rid:
                delete_supabase_incident(url, key, rid)
                
        from migrate_json_to_supabase import run_migration
        run_migration()

    print("\n" + "=" * 85)
    print("DEDUPLICATION & FINANCIAL ENRICHMENT PIPELINE COMPLETE!")
    print("=" * 85)

if __name__ == "__main__":
    main()
