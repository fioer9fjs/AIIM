"""
One-Click JSON-to-Supabase PostgreSQL Data Migration & Telemetry Script.
Reads all existing incidents and Knowledge Graph edges from static JSON files,
deduplicates incident_id keys in the batch payload, and uploads them into Supabase PostgreSQL.
Includes telemetry tracking for daily source ingestion statistics.
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import List, Dict, Any

def load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("\"'")

def get_supabase_credentials():
    load_env_file()
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SECRET_KEY", "")
    
    if not url or not key:
        print("--> [SECURITY NOTE] SUPABASE_URL or SUPABASE_SECRET_KEY missing from environment.")
        return url, ""
        
    if not key.startswith("sb_secret_"):
        print(f"--> [SECURITY ERROR] Invalid key format: SUPABASE_SECRET_KEY must start with 'sb_secret_'.")
        return url, ""
            
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
                print(f"Successfully updated Supabase table '{table_name}'!")
                return True
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode('utf-8')
        except Exception:
            pass
            
        if e.code == 404 and "PGRST205" in error_body:
            print(f"--> [NOTICE] Supabase table '{table_name}' does not exist yet. Run SQL in supabase_schema.sql to create it.")
            return False

        print(f"Error uploading to Supabase table '{table_name}': HTTP Error {e.code}: {e.reason}")
        if error_body:
            print(f"--> Supabase Error Details: {error_body}")
    except Exception as e:
        print(f"Error uploading to Supabase table '{table_name}': {e}")
        
    return False

def record_daily_source_stats(
    stat_date: str,
    rss_count: int = 0,
    gdelt_count: int = 0,
    arxiv_count: int = 0,
    aiid_count: int = 0,
    total_fetched: int = 0,
    passed_filter: int = 0,
    extracted_incidents: int = 0
):
    """Upserts daily telemetry metrics regarding source breakdown and ingestion health into Supabase."""
    url, key = get_supabase_credentials()
    if not url or not key:
        return
        
    record = [{
        "stat_date": stat_date,
        "rss_count": rss_count,
        "gdelt_count": gdelt_count,
        "arxiv_count": arxiv_count,
        "aiid_count": aiid_count,
        "total_fetched": total_fetched,
        "passed_filter": passed_filter,
        "extracted_incidents": extracted_incidents
    }]
    post_to_supabase_table(url, key, "daily_source_stats", record, "stat_date")

try:
    from scripts.ingest import consolidate_dataset
except ImportError:
    from ingest import consolidate_dataset

def sync_supabase_records(url: str, key: str, table_name: str, records: List[Dict[str, Any]], primary_key: str) -> bool:
    if not url or not key or not records:
        print(f"Skipping {table_name}: Missing Supabase credentials or empty records.")
        return False
        
    # 1. Upsert all canonical records
    ok = post_to_supabase_table(url, key, table_name, records, primary_key)
    if not ok:
        return False
        
    # 2. Fetch existing IDs from Supabase and delete any obsolete merged duplicates
    try:
        valid_ids = {r[primary_key] for r in records if r.get(primary_key)}
        get_req = urllib.request.Request(
            f"{url.rstrip('/')}/rest/v1/{table_name}?select={primary_key}",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}"
            },
            method="GET"
        )
        with urllib.request.urlopen(get_req) as resp:
            if resp.status == 200:
                remote_rows = json.loads(resp.read().decode("utf-8"))
                remote_ids = {row[primary_key] for row in remote_rows if primary_key in row}
                obsolete_ids = remote_ids - valid_ids
                if obsolete_ids:
                    print(f"--> Cleaning {len(obsolete_ids)} obsolete merged duplicates from Supabase table '{table_name}'...")
                    for obs_id in obsolete_ids:
                        del_req = urllib.request.Request(
                            f"{url.rstrip('/')}/rest/v1/{table_name}?{primary_key}=eq.{urllib.parse.quote(obs_id)}",
                            headers={
                                "apikey": key,
                                "Authorization": f"Bearer {key}"
                            },
                            method="DELETE"
                        )
                        try:
                            with urllib.request.urlopen(del_req):
                                pass
                        except Exception:
                            pass
                    print(f"--> Supabase table '{table_name}' is now strictly in sync with canonical dataset!")
    except Exception as e:
        print(f"Note on Supabase sync cleanup: {e}")
        
    return True

def run_migration():
    print("=" * 80)
    print("MIGRATING LOCAL JSON DATASET TO SUPABASE POSTGRESQL DATABASE")
    print("=" * 80)
    
    url, key = get_supabase_credentials()
    if not url or not key:
        print("\n[NOTE] SUPABASE_URL and SUPABASE_SECRET_KEY environment variables not set.")
        print("Set SUPABASE_URL and SUPABASE_SECRET_KEY to execute migration to live Supabase cloud.\n")
        return
        
    base_dir = os.path.join(os.path.dirname(__file__), "..", "src", "data")
    incidents_file = os.path.join(base_dir, "incidents.json")
    edges_file = os.path.join(base_dir, "edges.json")
    
    valid_incident_ids = set()
    supabase_incidents = []
    
    if os.path.exists(incidents_file):
        with open(incidents_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        seen_incident_ids = set()
        api_key = os.environ.get("GEMINI_API_KEY", "")
        # Run global deduplication consolidation pass via pure LLM
        incidents_data = consolidate_dataset(raw_data, api_key=api_key)
        with open(incidents_file, "w", encoding="utf-8") as f:
            json.dump(incidents_data, f, indent=2, ensure_ascii=False)
            
        for inc in incidents_data:
            iid = inc.get("incident_id")
            if not iid or iid in seen_incident_ids:
                continue
                
            seen_incident_ids.add(iid)
            valid_incident_ids.add(iid)
            
            date_val = str(inc.get("date", "2026-08-14")).strip()
            if len(date_val) > 10:
                date_val = date_val[:10]
            if not date_val or "-" not in date_val:
                date_val = "2026-08-14"
                
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
                "natsec_impact": inc.get("natsec_impact"),
                "impact_scope": inc.get("impact_scope"),
                "valuation_methodology": inc.get("valuation_methodology"),
                "source_type": inc.get("source_type", "google_news_rss"),
                "financial_damage_usd": inc.get("financial_damage_usd", 0)
            }
            
            row = {
                "incident_id": iid,
                "title": inc.get("title", ""),
                "summary": inc.get("summary", ""),
                "full_text": inc.get("full_text"),
                "date": date_val,
                "verification_status": inc.get("verification_status", "confirmed"),
                "severity": inc.get("severity", "medium"),
                "source_type": inc.get("source_type", "google_news_rss"),
                "financial_damage_usd": inc.get("financial_damage_usd", 0),
                "taxonomy": taxonomy_obj,
                "confidence_scores": inc.get("confidence_scores", {}),
                "geographic_scope": inc.get("geographic_scope", []),
                "affected_parties": inc.get("affected_parties", []),
                "source_urls": inc.get("source_urls", []),
                "related_incidents": inc.get("related_incidents", [])
            }
            supabase_incidents.append(row)
            
        print(f"Prepared {len(supabase_incidents)} unique incident records. Uploading to 'incidents' table...")
        sync_supabase_records(url, key, "incidents", supabase_incidents, "incident_id")

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
        sync_supabase_records(url, key, "edges", supabase_edges, "edge_id")
        
    print("\n" + "=" * 80)
    print("MIGRATION FINISHED!")
    print("=" * 80)

if __name__ == "__main__":
    run_migration()
