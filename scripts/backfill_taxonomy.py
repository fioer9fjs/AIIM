#!/usr/bin/env python3
"""
Backfill script to enrich historical incidents with Gemma/Gemini extended taxonomy:
- intent
- eu_ai_act_tier
- nist_ai_rmf_function
- iso_42001_category
- lifecycle_phase
- root_cause_category & subtype
- natsec_impact
"""

import json
import os
import sys
import time
from typing import Dict, Any

# Ensure scripts directory is in python path
sys.path.append(os.path.dirname(__file__))

from ingest import stage3_extract_taxonomy, assign_compliance_frameworks, assign_impact_scope, estimate_financial_damage
from migrate_json_to_supabase import run_migration

def run_backfill():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Check if .env file exists
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_file):
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.strip().split("=", 1)[1].strip("\"'")
                        break

    if not api_key:
        print("[ERROR] GEMINI_API_KEY environment variable not found! Cannot run LLM backfill.")
        sys.exit(1)

    json_path = os.path.join(os.path.dirname(__file__), "..", "src", "data", "incidents.json")
    with open(json_path, "r", encoding="utf-8") as f:
        incidents = json.load(f)

    total = len(incidents)
    incomplete = [inc for inc in incidents if inc.get("intent") is None or inc.get("eu_ai_act_tier") is None]
    print(f"Loaded {total} incidents from dataset. {len(incomplete)} incidents require Gemma taxonomy enrichment.\n")

    enriched_count = 0
    for idx, inc in enumerate(incidents):
        if inc.get("intent") is not None and inc.get("eu_ai_act_tier") is not None:
            continue

        title = inc.get("title", "")
        summary = inc.get("summary", "") or inc.get("full_text", "")
        inc_id = inc.get("incident_id", f"INC-{idx}")

        print(f"[{enriched_count + 1}/{len(incomplete)}] Enriching '{inc_id}': {title[:50]}...", flush=True)

        extracted = stage3_extract_taxonomy(title, summary, api_key=api_key)
        if isinstance(extracted, list) and len(extracted) > 0 and isinstance(extracted[0], dict):
            extracted = extracted[0]

        if extracted and isinstance(extracted, dict):
            # Merge missing taxonomy fields into existing incident object
            for key in ["intent", "lifecycle_phase", "eu_ai_act_tier", "nist_ai_rmf_function", "iso_42001_category", "root_cause_category", "root_cause_subtype", "natsec_impact", "failure_mode", "system_classification", "primary_purpose", "harm_domain", "harm_type"]:
                val = extracted.get(key)
                if val is not None and val != "":
                    inc[key] = val

            assign_compliance_frameworks(inc)
            assign_impact_scope(inc)

            # Ensure financial damage is present
            if not inc.get("financial_damage_usd") or inc.get("financial_damage_usd") == 0:
                usd, methodology = estimate_financial_damage(inc)
                inc["financial_damage_usd"] = usd
                inc["valuation_methodology"] = methodology

            enriched_count += 1
            print(f"  --> [SUCCESS] Intent: {inc.get('intent')} | EU: {inc.get('eu_ai_act_tier')} | NIST: {inc.get('nist_ai_rmf_function')}", flush=True)

            # Save progress incrementally to avoid losing state if interrupted
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(incidents, f, indent=2, ensure_ascii=False)

            time.sleep(1.5)  # Rate limiting safety delay
        else:
            print(f"  --> [WARNING] Gemma taxonomy extraction failed for '{inc_id}'. Skipping.")

    print(f"\n================================================================================")
    print(f"BACKFILL COMPLETE: Successfully enriched {enriched_count} incidents.")
    print(f"================================================================================")

    print("\nMigrating 100% enriched dataset to Supabase PostgreSQL database...")
    run_migration()

if __name__ == "__main__":
    run_backfill()
