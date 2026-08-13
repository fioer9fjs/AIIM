"""
One-Click JSON-to-Supabase PostgreSQL Data Migration Script.
Reads all existing incidents and Knowledge Graph edges from static JSON files
and uploads them seamlessly into Supabase PostgreSQL tables using REST API.
"""

import os
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any

def get_supabase_credentials():
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or os.environ.get("SUPABASE_KEY", "")
    return url, key

def post_to_supabase_table(url: str, key: str, table_name: str, records: List[Dict[str, Any]]) -> bool:
    if not url or not key or not records:
        print(f"Skipping {table_name}: Missing Supabase credentials or empty records.")
        return False
        
    endpoint = f"{url.rstrip('/')}/rest/v1/{table_name}"
    data_bytes = json.dumps(records).encode("utf-8")
    
    req = urllib.request.Request(
        endpoint,
        data=data_bytes,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates" # Upsert behavior
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status in (200, 201, 204):
                print(f"Successfully migrated {len(records)} records to Supabase table '{table_name}'!")
                return True
    except Exception as e:
        print(f"Error uploading to Supabase table '{table_name}': {e}")
        
    return False

def run_migration():
    print("=" * 80)
    print("MIGRATING LOCAL JSON DATASET TO SUPABASE POSTGRESQL DATABASE")
    print("=" * 80)
    
    url, key = get_supabase_credentials()
    if not url or not key:
        print("\n[NOTE] SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables not set.")
        print("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to execute migration to live Supabase cloud.\n")
        return
        
    base_dir = os.path.join(os.path.dirname(__file__), "..", "src", "data")
    incidents_file = os.path.join(base_dir, "incidents.json")
    edges_file = os.path.join(base_dir, "edges.json")
    
    if os.path.exists(incidents_file):
        with open(incidents_file, "r", encoding="utf-8") as f:
            incidents_data = json.load(f)
            
        supabase_incidents = []
        for inc in incidents_data:
            # Map core fields to SQL columns and taxonomy fields to JSONB
            taxonomy_obj = {
                "lifecycle_phase": inc.get("lifecycle_phase"),
                "system_classification": inc.get("system_classification"),
                "root_cause_category": inc.get("root_cause_category"),
                "root_cause_subtype": inc.get("root_cause_subtype"),
                "failure_mode": inc.get("failure_mode"),
                "harm_domain": inc.get("harm_domain"),
                "temporality": inc.get("temporality"),
                "intent": inc.get("intent"),
                "primary_purpose": inc.get("primary_purpose"),
                "harm_type": inc.get("harm_type"),
                "eu_ai_act_tier": inc.get("eu_ai_act_tier"),
                "natsec_impact": inc.get("natsec_impact")
            }
            
            row = {
                "incident_id": inc.get("incident_id"),
                "title": inc.get("title"),
                "summary": inc.get("summary"),
                "full_text": inc.get("full_text"),
                "date": inc.get("date"),
                "verification_status": inc.get("verification_status"),
                "severity": inc.get("severity"),
                "taxonomy": taxonomy_obj,
                "confidence_scores": inc.get("confidence_scores", {}),
                "geographic_scope": inc.get("geographic_scope", []),
                "affected_parties": inc.get("affected_parties", []),
                "source_urls": inc.get("source_urls", []),
                "related_incidents": inc.get("related_incidents", [])
            }
            supabase_incidents.append(row)
            
        post_to_supabase_table(url, key, "incidents", supabase_incidents)

    if os.path.exists(edges_file):
        with open(edges_file, "r", encoding="utf-8") as f:
            edges_data = json.load(f)
            
        supabase_edges = []
        for edge in edges_data:
            row = {
                "edge_id": edge.get("edge_id"),
                "source_id": edge.get("source_id"),
                "target_id": edge.get("target_id"),
                "relation_type": edge.get("relation_type"),
                "description": edge.get("description"),
                "confidence": edge.get("confidence", 0.90)
            }
            supabase_edges.append(row)
            
        post_to_supabase_table(url, key, "edges", supabase_edges)
        
    print("\n" + "=" * 80)
    print("MIGRATION FINISHED!")
    print("=" * 80)

if __name__ == "__main__":
    run_migration()
