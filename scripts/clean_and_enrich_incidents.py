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
    key = os.environ.get("SUPABASE_SECRET_KEY", "")
    if not key or not key.startswith("sb_secret_"):
        return url, ""
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
    if not isinstance(inc, dict):
        return
    title = (inc.get("title") or "").lower()

    summary = (inc.get("summary") or "").lower()
    rc = (inc.get("root_cause_category") or "").lower()
    sys_cls = (inc.get("system_classification") or "").lower()
    harm_type = (inc.get("harm_type") or "").lower()
    purpose = (inc.get("primary_purpose") or "").lower()
    
    if "governance" in rc or "policy" in summary or "legal" in summary or "court" in title or bool(re.search(r'\b(fcc|sec)\b', title)):
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

MACRO_KEYWORDS = [
    "annual report", "chainalysis", "interpol", "global losses", "across industry", "industry report",
    "trm labs", "certik", "first half of", "second half of", "half of 20", "stole during", "stolen during",
    "stole in 20", "stolen in 20", "total losses", "total theft", "multiple incidents", "incidents causing",
    "insiden peretasan", "pencurian aset", "66% of global", "global digital asset"
]

def assign_impact_scope(inc: Dict[str, Any]):
    """Assigns impact_scope ('discrete_incident' | 'cumulative_macro_trend')."""
    text_corpus = f"{inc.get('title', '')} {inc.get('summary', '')} {inc.get('full_text', '')}".lower()
    
    llm_scope = inc.get("impact_scope") or (inc.get("taxonomy", {}).get("impact_scope") if isinstance(inc.get("taxonomy"), dict) else None)
    
    if llm_scope == "cumulative_macro_trend":
        scope = "cumulative_macro_trend"
    elif any(k in text_corpus for k in MACRO_KEYWORDS):
        scope = "cumulative_macro_trend"
    else:
        scope = "discrete_incident"
        
    inc["impact_scope"] = scope
    if isinstance(inc.get("taxonomy"), dict):
        inc["taxonomy"]["impact_scope"] = scope

NON_DAMAGE_PATTERNS = [
    re.compile(r'(?:valued\s+at|valuation\s+of|valuation\s+at|market\s+cap\w*\s+of)\s*(?:\$|usd\s*)?([0-9]+(?:\.[0-9]+)?)\s*(billion|million)?', re.IGNORECASE),
    re.compile(r'(?:raised|funding\s+round\s+of|series\s+[a-z]\s+of)\s*(?:\$|usd\s*)?([0-9]+(?:\.[0-9]+)?)\s*(billion|million)?', re.IGNORECASE),
    re.compile(r'(?:contract\s+bid|contract\s+worth|contract\s+evaluation\s+of|contract\s+for\s+[a-z]+|pentagon\s+contract|dod\s+contract|deal\s+with\s+disney|ip\s+licensing|licensing\s+deal|licensing\s+fee|(?:\$|usd\s*)[0-9]+(?:\.[0-9]+)?\s*(?:billion|million)\s+contract)\b', re.IGNORECASE),
    re.compile(r'ipo\s+prospectus|on-paper\s+loss|operating\s+loss|operating\s+expense|infrastructure\s+expenditure|infrastructure\s+plans', re.IGNORECASE),
    re.compile(r'congressional\s+inquiry|senator\s+scrutinizes', re.IGNORECASE),
]

EXPLICIT_LOSS_PATTERNS = [
    re.compile(r'(?:fined|fine\s+of|penalty\s+of|penalties\s+of|settlement\s+of|settled\s+for|stole|stolen|theft\s+of|losses\s+of|lost|loss\s+of|damages\s+of|defrauded\s+(?:of\s+)?|ransom\s+of|restitution\s+of|sued\s+for)\s*\$([0-9]+(?:\.[0-9]+)?)\s*(billion|million|k|thousand)?', re.IGNORECASE),
    re.compile(r'\$([0-9]+(?:\.[0-9]+)?)\s*(billion|million|k|thousand)?\s*(?:fine|penalty|penalties|settlement|theft|loss|in\s+damages|in\s+losses|stolen|ransom|restitution)', re.IGNORECASE),
]

def _parse_currency_amount(val_str: str, unit_str: str) -> int:
    try:
        val = float(val_str)
        unit = (unit_str or "").lower()
        if unit == "billion":
            return int(val * 1_000_000_000)
        elif unit == "million":
            return int(val * 1_000_000)
        elif unit in ("k", "thousand"):
            return int(val * 1_000)
        return int(val)
    except Exception:
        return 0

LEGACY_SYNTHETIC_FALLBACKS = {
    2_500_000, 850_000, 12_500_000, 5_000_000, 280_000, 500_000, 450_000,
    1_200_000, 350_000, 4_500_000, 4_880_000, 6_800_000, 20_000_000, 15_000_000, 200_000_000
}

def _verify_number_in_text(usd: int, text: str) -> bool:
    if usd <= 0:
        return False
    if usd >= 1_000_000_000:
        b_val = usd / 1_000_000_000
        b_str = f"{b_val:.1f}" if b_val != int(b_val) else str(int(b_val))
        patterns = [f"{b_str} billion", f"${b_str} billion", f"${b_str}b", f"{usd:,}"]
    elif usd >= 1_000_000:
        m_val = usd / 1_000_000
        m_str = f"{m_val:.2f}".rstrip('0').rstrip('.') if m_val != int(m_val) else str(int(m_val))
        patterns = [f"{m_str} million", f"${m_str} million", f"${m_str}m", f"{m_str}m", f"{usd:,}"]
    elif usd >= 1_000:
        k_val = usd / 1_000
        k_str = f"{k_val:.1f}".rstrip('0').rstrip('.') if k_val != int(k_val) else str(int(k_val))
        patterns = [f"{k_str}k", f"${k_str}k", f"{k_str} thousand", f"{usd:,}", str(int(usd))]
    else:
        patterns = [str(int(usd))]
    return any(p in text for p in patterns)

def estimate_financial_damage(inc: Dict[str, Any]) -> Tuple[int, str]:
    """
    Evidence-Only Financial Damage Valuation.
    Returns (usd, methodology).
    
    Invariant:
    An incident receives financial_damage_usd > 0 if and only if explicit monetary loss,
    theft, fine, settlement, or damages demand is stated in the article text.
    Corporate balance-sheet metrics (operating loss, IPO valuation, infrastructure spend,
    licensing agreements, procurement contracts) are strictly excluded.
    Otherwise returns (0, "unquantified").
    """
    if inc.get("source_type") == "arxiv":
        return 0, "theoretical_academic"

    text_corpus = f"{inc.get('title', '')} {inc.get('summary', '')} {inc.get('full_text', '')}".lower()
    
    # Rejection of non-damage corporate finance, contracts, and inquiry letters
    if any(p.search(text_corpus) for p in NON_DAMAGE_PATTERNS):
        return 0, "unquantified"

    # 1. Check existing financial_damage_usd from LLM or previous persistence
    existing_usd = inc.get("financial_damage_usd", 0) or 0
    if isinstance(inc.get("taxonomy"), dict) and not existing_usd:
        existing_usd = inc["taxonomy"].get("financial_damage_usd", 0) or 0

    if existing_usd > 0:
        if existing_usd in LEGACY_SYNTHETIC_FALLBACKS or not _verify_number_in_text(existing_usd, text_corpus):
            existing_usd = 0

    if existing_usd > 0:
        if inc.get("impact_scope") == "cumulative_macro_trend":
            return existing_usd, "macro_statistic"
        return existing_usd, "explicit_confirmed"

    # 2. Strict regex check for explicit loss/fine/theft in article text
    for dmg_pat in EXPLICIT_LOSS_PATTERNS:
        match = dmg_pat.search(text_corpus)
        if match:
            extracted_usd = _parse_currency_amount(match.group(1), match.group(2))
            if extracted_usd > 0:
                if inc.get("impact_scope") == "cumulative_macro_trend":
                    return extracted_usd, "macro_statistic"
                return extracted_usd, "explicit_confirmed"

    # 3. No explicit evidence -> strictly 0 ("unquantified")
    return 0, "unquantified"

def main():
    print("=" * 85)
    print("GLOBAL AI INCIDENT MONITOR - DEDUPLICATION & FINANCIAL ENRICHMENT PIPELINE")
    print("=" * 85)

    data_dir = os.path.join(os.path.dirname(__file__), "..", "src", "data")
    incidents_path = os.path.join(data_dir, "incidents.json")

    url, key = get_supabase_credentials()
    db_incidents = fetch_supabase_incidents(url, key) if (url and key) else []

    incidents = []
    if os.path.exists(incidents_path):
        with open(incidents_path, "r", encoding="utf-8") as f:
            incidents = json.load(f)
        print(f"Loaded {len(incidents)} records from local incidents.json.")
        
        # Also merge any Supabase records that might not be in local JSON
        existing_urls = set()
        for inc in incidents:
            for u in inc.get("source_urls", []) or []:
                existing_urls.add(u.strip().lower())
            if inc.get("example_url"):
                existing_urls.add(inc["example_url"].strip().lower())
        
        added_from_db = 0
        for inc in db_incidents:
            u = (inc.get("example_url") or "").strip().lower()
            if u and u not in existing_urls:
                incidents.append(inc)
                existing_urls.add(u)
                added_from_db += 1
        if added_from_db > 0:
            print(f"Merged {added_from_db} additional records from Supabase PostgreSQL.")
    elif db_incidents:
        print(f"Loaded {len(db_incidents)} records from Supabase PostgreSQL.")
        incidents = db_incidents
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
