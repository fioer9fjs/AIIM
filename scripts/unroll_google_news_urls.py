"""
Script to resolve and unwrap all news.google.com RSS redirect URLs into direct original publisher URLs.
Updates src/data/incidents.json and Supabase PostgreSQL database.
"""

import os
import json
import time
from typing import List, Dict, Any
from googlenewsdecoder import new_decoderv1

def get_supabase_credentials():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or os.environ.get("SUPABASE_KEY", "")
    return url, key

def unwrap_url(url: str) -> str:
    if "news.google.com" not in url:
        return url
    try:
        res = new_decoderv1(url)
        if isinstance(res, dict) and res.get("status") and res.get("decoded_url"):
            decoded = res["decoded_url"]
            if "news.google.com" not in decoded:
                return decoded
    except Exception as e:
        print(f"Decoder note for {url[:40]}: {e}")
    return url

def main():
    print("=" * 85)
    print("UNWRAPPING GOOGLE NEWS REDIRECT URLS TO ORIGINAL PUBLISHER ARTICLES")
    print("=" * 85)

    data_dir = os.path.join(os.path.dirname(__file__), "..", "src", "data")
    incidents_path = os.path.join(data_dir, "incidents.json")

    if not os.path.exists(incidents_path):
        print("incidents.json not found.")
        return

    with open(incidents_path, "r", encoding="utf-8") as f:
        incidents: List[Dict[str, Any]] = json.load(f)

    unrolled_count = 0
    total_urls = 0

    for inc in incidents:
        urls = inc.get("source_urls", []) or []
        new_urls = []
        for u in urls:
            total_urls += 1
            if "news.google.com" in u:
                real_url = unwrap_url(u)
                if real_url != u:
                    unrolled_count += 1
                    print(f"  [UNROLLED] '{inc.get('title')[:40]}...' -> {real_url}")
                    new_urls.append(real_url)
                else:
                    new_urls.append(u)
            else:
                new_urls.append(u)
        inc["source_urls"] = list(dict.fromkeys(new_urls))

    with open(incidents_path, "w", encoding="utf-8") as f:
        json.dump(incidents, f, indent=2)

    print(f"\nUnwrapped {unrolled_count} out of {total_urls} Google News URLs into direct publisher links!")
    print(f"Saved updated incidents.json.")

    # Synchronize to Supabase PostgreSQL
    url, key = get_supabase_credentials()
    if url and key:
        print("\n---> SYNCHRONIZING UNWRAPPED URLS TO SUPABASE POSTGRESQL...")
        from migrate_json_to_supabase import run_migration
        run_migration()

if __name__ == "__main__":
    main()
