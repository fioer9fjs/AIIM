"""
One-Click JSON-to-Supabase PostgreSQL Data Migration Script.
Reads all existing incidents and Knowledge Graph edges from static JSON files,
deduplicates incident_id keys in the batch payload, and uploads them into Supabase PostgreSQL.
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import List, Dict, Any

def get_supabase_credentials():
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or os.environ.get("SUPABASE_KEY", "")
    return url, key

def post_to_supabase_table(url: str, key: str, table_name: str, records: List[Dict[str, Any]], primary_key: str) -> bool:
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
            "Prefer": f"resolution=merge-duplicates,on_conflict={primary_key}"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status in (200, 201, 204):
                print(f"Successfully migrated {len(records)} records to Supabase table '{table_name}'!")
                return True
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode('utf-8')
        except Exception:
            pass
        print(f"Error uploading to Supabase table '{table_name}': HTTP Error {e.code}: {e.reason}")
        if error_body:
            print(f"--> Supabase Error Details: {error_body}")
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
    
    seen_incident_ids = set()
    valid_incident_ids = set()
    supabase_incidents = []
    
    if os.path.exists(incidents_file):
        with open(incidents_file, "r", encoding="utf-8") as f:
            incidents_data = json.load(f)
            
        idx_counter = 1
        for inc in incidents_data:
            iid = inc.get("incident_id")
            # If incident_id is missing or duplicate in local batch, re-assign clean unique ID
            if not iid or iid in seen_incident_ids:
                date_prefix = str(inc.get("date", "20260813")).replace("-", "")[:8]
                iid = f"INC-{date_prefix}-{idx_counter:03d}"
                idx_counter += 1
                
            seen_incident_ids.add(iid)
            valid_incident_ids.add(iid)
            
            # Clean and sanitize date to valid YYYY-MM-DD
            date_val = str(inc.get("date", "2026-08-13")).strip()
            if len(date_val) > 10:
                date_val = date_val[:10]
            if not date_val or "-" not in date_val:
                date_val = "2026-08-13"
                
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
                "incident_id": iid,
                "title": inc.get("title", ""),
                "summary": inc.get("summary", ""),
                "full_text": inc.get("full_text"),
                "date": date_val,
                "verification_status": inc.get("verification_status", "confirmed"),
                "severity": inc.get("severity", "medium"),
                "taxonomy": taxonomy_obj,
                "confidence_scores": inc.get("confidence_scores", {}),
                "geographic_scope": inc.get("geographic_scope", []),
                "affected_parties": inc.get("affected_parties", []),
                "source_urls": inc.get("source_urls", []),
                "related_incidents": inc.get("related_incidents", [])
            }
            supabase_incidents.append(row)
            
        print(f"Prepared {len(supabase_incidents)} unique incident records. Uploading to 'incidents' table...")
        post_to_supabase_table(url, key, "incidents", supabase_incidents, "incident_id")

    if os.path.exists(edges_file):
        with open(edges_file, "r", encoding="utf-8") as f:
            edges_data = json.load(f)
            
        seen_edge_ids = set()
        supabase_edges = []
        edge_idx = 1
        for edge in edges_data:
            eid = edge.get("edge_id")
            if not eid or eid in seen_edge_ids:
                eid = f"EDGE-{edge_idx:03d}"
                
            seen_edge_ids.add(eid)
            edge_idx += 1
            
            src = edge.get("source_id")
            tgt = edge.get("target_id")
            
            # Ensure both source and target exist in validated incidents
            if src in valid_incident_ids and tgt in valid_incident_ids:
                row = {
                    "edge_id": eid,
                    "source_id": src,
                    "target_id": tgt,
                    "relation_type": edge.get("relation_type", "related_cause"),
                    "description": edge.get("description", ""),
                    "confidence": edge.get("confidence", 0.90)
                }
                supabase_edges.append(row)
            
        print(f"Prepared {len(supabase_edges)} valid graph edge records. Uploading to 'edges' table...")
        post_to_supabase_table(url, key, "edges", supabase_edges, "edge_id")
        
    print("\n" + "=" * 80)
    print("MIGRATION FINISHED!")
    print("=" * 80)

if __name__ == "__main__":
    run_migration()
