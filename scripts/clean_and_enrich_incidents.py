"""
Comprehensive One-Click Incident Deduplication, Cross-Date Merging & Financial Damage Enrichment Script.

1. Fetches all incidents from local dataset / Supabase PostgreSQL.
2. Performs cross-date fuzzy similarity matching across titles, summaries, and affected entities.
3. Merges duplicate incidents across dates, combining source_urls and preserving canonical earliest dates.
4. Uses Gemini 3.6 Flash to re-evaluate and populate financial_damage_usd (applying the $12.5M VSL benchmark for fatalities).
5. Deletes duplicate records from Supabase PostgreSQL and updates clean dataset.
"""

import os
import json
import difflib
import time
import urllib.request
import urllib.parse
from typing import List, Dict, Any
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

def get_supabase_credentials():
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
    
    # Direct SequenceMatcher ratio on title
    title_ratio = difflib.SequenceMatcher(None, t1, t2).ratio()
    
    # Word set Jaccard similarity on summary
    words1 = set(inc1.get("summary", "").lower().split())
    words2 = set(inc2.get("summary", "").lower().split())
    jaccard_summary = len(words1.intersection(words2)) / float(max(len(words1.union(words2)), 1))
    
    # Affected parties overlap bonus
    parties1 = set(p.lower() for p in inc1.get("affected_parties", []))
    parties2 = set(p.lower() for p in inc2.get("affected_parties", []))
    party_overlap = 0.15 if (parties1 and parties2 and len(parties1.intersection(parties2)) > 0) else 0.0
    
    return (title_ratio * 0.5) + (jaccard_summary * 0.35) + party_overlap

def enrich_financial_damage(inc: Dict[str, Any], client: genai.Client) -> int:
    """Queries Gemini 3.6 Flash to extract or estimate financial_damage_usd for an incident."""
    title = inc.get("title", "")
    summary = inc.get("summary", "")
    full_text = inc.get("full_text", "")
    
    prompt = f"""
Analyze the following AI safety incident and determine the total financial impact in USD (financial_damage_usd).

INCIDENT TITLE: {title}
SUMMARY: {summary}
FULL TEXT CONTEXT: {full_text[:2000]}

FINANCIAL CALCULATION RULES:
1. If explicit dollar/euro amounts are stated in fines, settlements, stock losses, or fraud (e.g. $1.5 billion), return that exact integer in USD (1500000000).
2. If human life was lost or fatal physical harm occurred, apply the standard VSL (Value of a Statistical Life) benchmark of $12,500,000 USD (12500000) per fatality.
3. If no financial harm occurred or it is purely theoretical/latent research, return 0.

Return ONLY a valid JSON object matching this schema:
{{
  "financial_damage_usd": 15000000,
  "rationale": "Short explanation of calculation"
}}
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        if response and response.text:
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            data = json.loads(text.strip())
            return int(data.get("financial_damage_usd", 0))
    except Exception as e:
        print(f"Gemini enrichment note for '{title[:30]}...': {e}")
    return inc.get("financial_damage_usd", 0)

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
            if sim >= 0.52:  # Threshold for semantic duplication
                matched = True
                print(f"  [DUPLICATE MATCH ({sim:.2f})] Merging '{inc.get('title')[:45]}...' into '{target.get('title')[:45]}...'")
                removed_ids.append(inc.get("incident_id"))
                
                # Merge source_urls
                urls1 = target.get("source_urls", []) or []
                urls2 = inc.get("source_urls", []) or []
                combined_urls = list(dict.fromkeys(urls1 + urls2))
                target["source_urls"] = combined_urls
                
                # Preserve earliest date
                date1 = target.get("date", "2026-08-14")
                date2 = inc.get("date", "2026-08-14")
                if date2 < date1:
                    target["date"] = date2
                    
                # Retain highest damage if present
                d1 = target.get("financial_damage_usd", 0) or 0
                d2 = inc.get("financial_damage_usd", 0) or 0
                target["financial_damage_usd"] = max(d1, d2)
                
                # Prefer fuller text if available
                if not target.get("full_text") and inc.get("full_text"):
                    target["full_text"] = inc.get("full_text")
                    
                break

        if not matched:
            unique_incidents.append(inc)

    print(f"\nDeduplication complete: Reduced dataset from {len(incidents)} to {len(unique_incidents)} unique incidents (Removed {len(removed_ids)} duplicate records).")

    # 2. FINANCIAL DAMAGE ENRICHMENT WITH GEMINI
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if HAS_GENAI and api_key:
        print("\n---> ENRICHING FINANCIAL DAMAGE METRICS VIA GEMINI 3.6 FLASH...")
        client = genai.Client(api_key=api_key)
        enriched_count = 0
        for inc in unique_incidents:
            current_val = inc.get("financial_damage_usd", 0) or 0
            if current_val == 0:
                new_damage = enrich_financial_damage(inc, client)
                if new_damage > 0:
                    inc["financial_damage_usd"] = new_damage
                    if isinstance(inc.get("taxonomy"), dict):
                        inc["taxonomy"]["financial_damage_usd"] = new_damage
                    enriched_count += 1
                    print(f"  [ENRICHED] {inc.get('title')[:50]}... -> ${new_damage:,} USD")
                time.sleep(0.5)  # Rate limit protection
        print(f"Enriched financial damage metrics for {enriched_count} incidents.")

    # 3. SAVE CLEAN DATASET TO LOCAL JSON
    with open(incidents_path, "w", encoding="utf-8") as f:
        json.dump(unique_incidents, f, indent=2)
    print(f"\nSaved {len(unique_incidents)} cleaned & enriched records to {incidents_path}.")

    # 4. SYNC TO SUPABASE (DELETE DUPLICATES & UPSERT CLEAN DATASET)
    if url and key:
        print("\n---> SYNCHRONIZING CLEAN DATASET TO SUPABASE POSTGRESQL...")
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
