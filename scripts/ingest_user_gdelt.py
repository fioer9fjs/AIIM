"""
Dedicated GDELT JSON Ingestion Script for Global AI Incident Monitor.
Ingests candidate clusters directly exported from BigQuery query results.
Runs 3-Stage LLM Gatekeeper, Deep Taxonomy & Conservative Financial Valuation,
and syncs dataset to Supabase PostgreSQL Cloud DB.
"""

import sys
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
from scripts.ingest import process_article_3stage_pipeline
from scripts.clean_and_enrich_incidents import main as run_dedup_and_sync

USER_GDELT_JSON_PATH = "scratch/user_gdelt_export.json"
INCIDENTS_JSON_PATH = os.path.join("src", "data", "incidents.json")

def format_published_date(raw_date: str) -> str:
    """Formats GDELT 'YYYYMMDDHHMMSS' to 'YYYY-MM-DD'."""
    if not raw_date or len(raw_date) < 8:
        return datetime.now().strftime("%Y-%m-%d")
    try:
        dt = datetime.strptime(raw_date[:8], "%Y%m%d")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d")

def title_from_url(url: str) -> str:
    """Extracts human readable title from URL slug."""
    if not url:
        return "AI Incident Report"
    slug = url.split('/')[-1] or url.split('/')[-2]
    # Strip extensions or parameters
    slug = re.sub(r'\.(html|htm|php|aspx|axd)$', '', slug, flags=re.IGNORECASE)
    slug = re.sub(r'[\?#].*$', '', slug)
    words = [w.capitalize() for w in re.split(r'[-_]', slug) if len(w) > 1 and not w.isdigit()]
    return " ".join(words) if words else "AI Incident Report"

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable is missing!")
        return

    if not os.path.exists(USER_GDELT_JSON_PATH):
        print(f"ERROR: {USER_GDELT_JSON_PATH} not found!")
        return

    with open(USER_GDELT_JSON_PATH, "r", encoding="utf-8") as f:
        gdelt_items = json.load(f)

    print("================================================================================")
    print(f"INGESTING {len(gdelt_items)} GDELT BIGQUERY CANDIDATES INTO 3-STAGE PIPELINE")
    print("================================================================================")

    # Load existing incidents dataset
    existing_incidents = []
    if os.path.exists(INCIDENTS_JSON_PATH):
        with open(INCIDENTS_JSON_PATH, "r", encoding="utf-8") as f:
            existing_incidents = json.load(f)

    existing_urls = set()
    for inc in existing_incidents:
        for url in inc.get("source_urls", []):
            existing_urls.add(url.strip().lower())
        if inc.get("example_url"):
            existing_urls.add(inc["example_url"].strip().lower())

    passed_count = 0
    rejected_count = 0
    skipped_existing = 0

    for i, item in enumerate(gdelt_items, 1):
        url = item.get("example_url", "").strip()
        if not url:
            continue

        if url.lower() in existing_urls:
            skipped_existing += 1
            continue

        pub_date_clean = format_published_date(item.get("first_published", ""))
        inferred_title = title_from_url(url)
        reports_count = item.get("number_of_reports", 1)
        avg_tone = item.get("avg_tone", "-3.0")

        description_text = f"GDELT Clustered Event: Reported by {reports_count} global news outlets. Average tone: {avg_tone}. Samples: {', '.join(item.get('reported_by_samples', [])[:5])}"

        article_dict = {
            "title": inferred_title,
            "link": url,
            "pub_date_clean": pub_date_clean,
            "description": description_text,
            "source_type": "gdelt_bigquery"
        }

        print(f"\nProcessing [{i}/{len(gdelt_items)}]: {url[:70]}...")
        enriched = process_article_3stage_pipeline(article_dict, api_key)
        time.sleep(1.2)


        if enriched:
            # Generate unique ID
            inc_date = enriched.get("date", pub_date_clean).replace("-", "")
            enriched["id"] = f"INC-{inc_date}-{len(existing_incidents) + passed_count + 100:03d}"
            enriched["gdelt_report_count"] = reports_count
            existing_incidents.append(enriched)
            existing_urls.add(url.lower())
            passed_count += 1
        else:
            rejected_count += 1

    print("\n================================================================================")
    print(f"GDELT Ingestion Complete: {passed_count} passed & enriched, {rejected_count} rejected, {skipped_existing} skipped (already in DB).")
    print(f"Total dataset size: {len(existing_incidents)} records.")
    print("================================================================================")

    # Save to local JSON dataset
    with open(INCIDENTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(existing_incidents, f, indent=2, ensure_ascii=False)
    print(f"Saved dataset to {INCIDENTS_JSON_PATH}.")

    # Run Deduplication & Supabase PostgreSQL Sync
    print("\n---> Running Deduplication & Supabase Cloud PostgreSQL Sync...")
    run_dedup_and_sync()

if __name__ == "__main__":
    main()
