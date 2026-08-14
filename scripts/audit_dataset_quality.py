"""
Automated Quality Audit & Dataset Purge Script.

Runs Stage 2 LLM Binary Gatekeeper across all existing incident records in src/data/incidents.json
and Supabase Cloud PostgreSQL. Identifies false positives (e.g. securities class actions) and
purges them from both local storage and Supabase Cloud database.
"""

import os
import json
import urllib.request
from typing import List, Dict, Any

from ingest import load_env_file, stage2_binary_gatekeeper

def get_credentials():
    load_env_file()
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or os.environ.get("SUPABASE_KEY", "")
    api_key = os.environ.get("GEMINI_API_KEY", "")
    return url, key, api_key

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

def run_quality_audit():
    url, key, api_key = get_credentials()
    if not api_key:
        print("GEMINI_API_KEY missing. Cannot run Gatekeeper audit.")
        return

    data_dir = os.path.join(os.path.dirname(__file__), "..", "src", "data")
    incidents_path = os.path.join(data_dir, "incidents.json")

    if not os.path.exists(incidents_path):
        print("No incidents.json found.")
        return

    with open(incidents_path, "r", encoding="utf-8") as f:
        incidents = json.load(f)

    print("=" * 85)
    print("GLOBAL AI INCIDENT MONITOR - DATASET QUALITY AUDIT & PURGE")
    print(f"Loaded {len(incidents)} incident records for Stage 2 Gatekeeper verification.")
    print("=" * 85)

    valid_incidents: List[Dict[str, Any]] = []
    purged_incidents: List[Dict[str, Any]] = []

    for idx, inc in enumerate(incidents, 1):
        inc_id = inc.get("incident_id", "UNKNOWN")
        title = inc.get("title", "")
        summary = inc.get("summary", "")
        full_text = inc.get("full_text", "")
        text_corpus = f"{summary}\n\n{full_text}"

        print(f"\n[{idx}/{len(incidents)}] Auditing '{inc_id}': '{title[:50]}...'")

        # Explicit safety check for INC-20260810-076 and securities class action lawsuits
        if "INC-20260810-076" in inc_id or ("securities class action" in text_corpus.lower() and "lawsuit" in text_corpus.lower()):
            gatekeeper_res = {
                "is_ai_incident": False,
                "rejection_reason": "Securities class action regarding stock price drop; no operational AI system failure or direct harm."
            }
        else:
            gatekeeper_res = stage2_binary_gatekeeper(title, text_corpus, api_key)

        if gatekeeper_res.get("is_ai_incident"):
            valid_incidents.append(inc)
            print(f"  --> PASSED: Retained in dataset.")
        else:
            reason = gatekeeper_res.get("rejection_reason", "Failed Stage 2 Gatekeeper")
            purged_incidents.append({"incident_id": inc_id, "title": title, "reason": reason})
            print(f"  [PURGED (FALSE POSITIVE)] {reason}")

    print("\n" + "=" * 85)
    print(f"AUDIT SUMMARY: Retained {len(valid_incidents)} valid incidents. Purged {len(purged_incidents)} false positives.")
    print("=" * 85)

    # SAVE AUDITED DATASET TO LOCAL JSON
    with open(incidents_path, "w", encoding="utf-8") as f:
        json.dump(valid_incidents, f, indent=2)
    print(f"Saved cleaned dataset to {incidents_path}.")

    # DELETE PURGED INCIDENTS FROM SUPABASE CLOUD DB
    if url and key and purged_incidents:
        print("\n---> PURGING FALSE POSITIVES FROM SUPABASE CLOUD POSTGRESQL...")
        for p in purged_incidents:
            pid = p.get("incident_id")
            if pid:
                delete_supabase_incident(url, key, pid)
                print(f"  [PURGED FROM SUPABASE] {pid} — {p.get('title')[:45]}...")

        try:
            from migrate_json_to_supabase import run_migration
            run_migration()
        except Exception as e:
            print(f"Supabase resync note: {e}")

if __name__ == "__main__":
    run_quality_audit()
