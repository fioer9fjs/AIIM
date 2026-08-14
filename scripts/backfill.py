"""
Historical 7-Day Backfill Pipeline for Global AI Incident Monitor.
Dual GDELT Harvester (BigQuery + Rate-Protected API) & Google News RSS Decoder.
Loops day-by-day through the past 7 days, scrapes full text, extracts taxonomy via Gemini 3.6 Flash,
and updates incidents.json, edges.json AND records telemetry stats in Supabase table 'daily_source_stats'.
"""

import os
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

try:
    import requests
    from bs4 import BeautifulSoup
    from googlenewsdecoder import gnewsdecoder
    HAS_SCRAPER = True
except ImportError:
    HAS_SCRAPER = False

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    try:
        import google.generativeai as legacy_genai
        HAS_LEGACY_GENAI = True
    except ImportError:
        pass

try:
    from google.cloud import bigquery
    HAS_BIGQUERY = True
except ImportError:
    HAS_BIGQUERY = False

from taxonomy_filters import (
    TIER_1_MODELS_PRODUCTS,
    TIER_1_PROVIDERS,
    TIER_1_INCIDENT_TERMS,
    score_article_relevance
)

SYSTEM_PROMPT = """
You are an expert AI Safety & Regulatory Incident Analyst.
Analyze the following FULL-TEXT news article about an AI-related event and extract structured taxonomy metadata.

An "AI Incident" is an event/circumstance where the development, deployment, use, malfunction, or misuse of an AI system leads to actual harm, potential harm, security breach, bias, hallucination impact, or significant deviation from safe operation.

Return ONLY a valid JSON object matching this exact schema:
{
  "is_ai_incident": true/false,
  "title": "Concise factual incident title",
  "summary": "2-3 sentence executive summary of what happened, root causes, and impact",
  "date": "YYYY-MM-DD",
  "verification_status": "alleged" | "confirmed" | "disputed",
  "lifecycle_phase": "design_and_training" | "testing_and_validation" | "deployment_and_integration" | "operation_and_monitoring" | "decommissioning",
  "system_classification": "high_risk_regulated" | "general_purpose_model" | "autonomous_agent" | "biometric_identification" | "critical_infrastructure_component" | "dual_use_security" | "unclassified",
  "intent": "intentional_misuse" | "unintentional_failure",
  "primary_purpose": "generative_content" | "autonomous_mobility" | "biometric_surveillance" | "financial_fintech" | "healthcare_medical" | "recruitment_hr" | "defense_national_security" | "content_recommendation" | "other",
  "root_cause_category": "data" | "model" | "human" | "governance" | "external" | "undetermined",
  "root_cause_subtype": "hallucination/poisoning/bias/adversarial_attack/etc",
  "failure_mode": "Brief narrative connecting cause to consequence based on full text details",
  "harm_domain": "persons_physical" | "persons_mental" | "persons_rights" | "property" | "environment" | "systemic_integrity" | "societal",
  "harm_type": "discrimination_bias" | "privacy_breach" | "physical_safety" | "misinformation" | "economic_labor" | "copyright_ip" | "psychological_harm" | "national_security",
  "financial_damage_usd": 15000000, // Numeric total USD financial impact (fines, settlements, losses). For fatal harm or loss of human life, apply standard VSL (Value of a Statistical Life) benchmark of $12,500,000 USD per fatality.
  "eu_ai_act_tier": "prohibited" | "high_risk" | "limited_risk" | "minimal_risk",
  "natsec_impact": true/false,
  "temporality": "actual" | "potential" | "latent",
  "severity": "critical" | "high" | "medium" | "low",
  "confidence_scores": {
    "verification_status": 0.95,
    "lifecycle_phase": 0.90,
    "system_classification": 0.95,
    "root_cause_category": 0.90,
    "harm_domain": 0.95,
    "severity": 0.90
  },
  "geographic_scope": ["Country/Region"],
  "affected_parties": ["Entity1", "Entity2"]
}

If the text is NOT an AI incident, return: {"is_ai_incident": false}
"""

_WORKING_MODEL_NAME = None

PREFERRED_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.0-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash"
]

def fetch_full_text(url: str) -> str:
    if not url or not HAS_SCRAPER:
        return ""
        
    real_url = url
    try:
        if "news.google.com" in url:
            decoded = gnewsdecoder(url)
            if isinstance(decoded, dict) and decoded.get("status") and decoded.get("decoded_url"):
                real_url = decoded.get("decoded_url")
    except Exception:
        pass
        
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(real_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
                tag.extract()
            paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 35]
            full_text = "\n\n".join(paragraphs)
            return full_text if len(full_text) > 100 else ""
    except Exception:
        pass
        
    return ""

def process_article_with_gemini(article: Dict[str, str], api_key: str, target_date_str: str) -> Optional[Dict[str, Any]]:
    global _WORKING_MODEL_NAME
    if not api_key:
        return None
        
    full_text = fetch_full_text(article['link'])
    text_payload = full_text if full_text else article.get('description', '')
    prompt = f"{SYSTEM_PROMPT}\n\nARTICLE TITLE: {article['title']}\n\nARTICLE FULL TEXT:\n{text_payload[:12000]}"
    
    candidate_models = list(PREFERRED_MODELS)
    if _WORKING_MODEL_NAME and _WORKING_MODEL_NAME in candidate_models:
        candidate_models.remove(_WORKING_MODEL_NAME)
        candidate_models.insert(0, _WORKING_MODEL_NAME)

    text_clean = ""
    for model_name in candidate_models:
        if HAS_GENAI:
            try:
                from google.genai import types
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                if response and response.text:
                    text_clean = response.text.strip()
                    _WORKING_MODEL_NAME = model_name
                    break
            except Exception:
                continue

    if not text_clean:
        return None
        
    try:
        if text_clean.startswith("```json"):
            text_clean = text_clean[7:]
        if text_clean.endswith("```"):
            text_clean = text_clean[:-3]
        data = json.loads(text_clean.strip())
        if data.get("is_ai_incident"):
            data["source_urls"] = [article["link"]]
            data["source_type"] = article.get("source_type", "google_news_rss")
            if full_text:
                data["full_text"] = full_text[:4000]
                
            data["date"] = target_date_str
            return data
    except Exception:
        pass
        
    return None

def fetch_rss_for_date_range(query: str, target_date_str: str) -> List[Dict[str, Any]]:
    full_query = f"{query} after:{target_date_str} before:{(datetime.strptime(target_date_str, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')}"
    encoded_query = urllib.parse.quote(full_query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    articles = []
    try:
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            for item in root.findall('./channel/item')[:6]:
                title = item.find('title').text if item.find('title') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                description = item.find('description').text if item.find('description') is not None else ""
                
                articles.append({
                    "title": title,
                    "link": link,
                    "pub_date": pub_date,
                    "description": description,
                    "source_type": "google_news_rss"
                })
    except Exception:
        pass
    return articles

def fetch_gdelt_bigquery_for_date(target_date_str: str, max_items: int = 10) -> List[Dict[str, Any]]:
    """Queries GDELT BigQuery partitioned table for a historical target date (YYYY-MM-DD)."""
    if not HAS_BIGQUERY:
        return []
        
    articles = []
    try:
        project_id = os.environ.get("GCP_PROJECT_ID")
        client = bigquery.Client(project=project_id) if project_id else bigquery.Client()
        sql = f"""
        SELECT 
            DocumentIdentifier as link,
            SourceCommonName as domain
        FROM `gdelt-bq.gdeltv2.gkg_partitioned`
        WHERE _PARTITIONDATE = '{target_date_str}'
          AND (
            LOWER(V2Themes) LIKE '%artificial_intelligence%' 
            OR LOWER(V2Themes) LIKE '%cyber_attack%'
            OR LOWER(V2Themes) LIKE '%lawsuit%'
          )
        LIMIT {max_items};
        """
        query_job = client.query(sql)
        for row in query_job.result():
            articles.append({
                "title": f"AI News Event from {row.domain}",
                "link": row.link,
                "pub_date": target_date_str,
                "description": f"GDELT BigQuery event from {row.domain}",
                "source_type": "gdelt"
            })
    except Exception as e:
        print(f"BigQuery GDELT Harvester note for {target_date_str}: {e}")
    return articles

def fetch_gdelt_api_for_date(query: str, target_date_str: str) -> List[Dict[str, Any]]:
    """Fetches articles from GDELT REST API for a historical date with rate limit backoff."""
    date_compact = target_date_str.replace("-", "")
    start_dt = f"{date_compact}000000"
    end_dt = f"{date_compact}235959"
    encoded_query = urllib.parse.quote(query)
    gdelt_url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={encoded_query}&mode=ArtList&maxrecords=3&format=json&startdatetime={start_dt}&enddatetime={end_dt}"
    articles = []
    
    for attempt in range(2):
        try:
            req = urllib.request.Request(gdelt_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                for art in data.get('articles', []):
                    articles.append({
                        "title": art.get("title", ""),
                        "link": art.get("url", ""),
                        "pub_date": target_date_str,
                        "description": art.get("title", ""),
                        "source_type": "gdelt"
                    })
                break
        except Exception as e:
            if "429" in str(e):
                time.sleep(2)
            else:
                break
    return articles

def save_to_incidents_json(new_incidents: List[Dict[str, Any]]) -> int:
    if not new_incidents:
        return 0
        
    data_dir = os.path.join(os.path.dirname(__file__), "..", "src", "data")
    incidents_path = os.path.join(data_dir, "incidents.json")
    
    existing = []
    if os.path.exists(incidents_path):
        try:
            with open(incidents_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []
            
    existing_titles = set(i.get("title", "").lower() for i in existing)
    
    added_count = 0
    for inc in new_incidents:
        title = inc.get("title", "")
        if title and title.lower() not in existing_titles:
            date_prefix = str(inc.get("date", "20260814")).replace("-", "")[:8]
            inc["incident_id"] = f"INC-{date_prefix}-{len(existing) + added_count + 1:03d}"
            if "related_incidents" not in inc:
                inc["related_incidents"] = []
            existing.insert(0, inc)
            existing_titles.add(title.lower())
            added_count += 1
            
    if added_count > 0 or existing:
        with open(incidents_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
            
        try:
            from migrate_json_to_supabase import run_migration
            run_migration()
        except Exception as e:
            print(f"Note on Supabase sync: {e}")
            
    return added_count

def run_7day_backfill():
    print("=" * 85)
    print("GLOBAL AI INCIDENT MONITOR - DUAL GDELT (BIGQUERY + API) 7-DAY BACKFILL")
    print("=" * 85)
    
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("GEMINI_API_KEY environment variable not set. Please set key to run backfill.")
        return
        
    queries = [
        f'({ " OR ".join(TIER_1_MODELS_PRODUCTS[:6]) }) ({ " OR ".join(TIER_1_INCIDENT_TERMS[:6]) })',
        f'("AI incident" OR "LLM vulnerability" OR "deepfake fraud")',
        f'("EU AI Act violation" OR "GDPR AI fine" OR "AI copyright lawsuit")'
    ]
    
    total_added = 0
    today = datetime.now()
    
    for day_offset in range(1, 8):
        target_date = today - timedelta(days=day_offset)
        date_str = target_date.strftime("%Y-%m-%d")
        print(f"\n---> PROCESSING HISTORICAL DAY: {date_str} (Day -{day_offset})")
        
        day_articles = []
        rss_count = 0
        gdelt_count = 0
        
        # 1. Try GDELT BigQuery for day
        bq_arts = fetch_gdelt_bigquery_for_date(date_str)
        if bq_arts:
            gdelt_count += len(bq_arts)
            day_articles.extend(bq_arts)
            
        # 2. Fetch RSS & GDELT API
        for q in queries:
            rss_arts = fetch_rss_for_date_range(q, date_str)
            rss_count += len(rss_arts)
            day_articles.extend(rss_arts)
            
            if not bq_arts:
                gdelt_api_arts = fetch_gdelt_api_for_date(q, date_str)
                gdelt_count += len(gdelt_api_arts)
                day_articles.extend(gdelt_api_arts)
                time.sleep(1) # Rate limit protection
                
        passed_articles = [a for a in day_articles if score_article_relevance(a['title'], a.get('description', '')) >= 0.4]
        print(f"     Fetched {len(day_articles)} raw news items (RSS: {rss_count}, GDELT: {gdelt_count}) -> {len(passed_articles)} passed relevance filter.")
        
        day_extracted = []
        for art in passed_articles:
            inc = process_article_with_gemini(art, api_key, date_str)
            if inc and inc.get("is_ai_incident"):
                day_extracted.append(inc)
                print(f"     [EXTRACTED - {inc.get('source_type')}] {inc.get('title')} | Text Length: {len(inc.get('full_text', ''))} chars")
                
        added = save_to_incidents_json(day_extracted)
        total_added += added
        print(f"     Saved {added} new incidents for {date_str}.")
        
        # Record Telemetry Stats for Backfill Day
        try:
            from migrate_json_to_supabase import record_daily_source_stats
            record_daily_source_stats(
                stat_date=date_str,
                rss_count=rss_count,
                gdelt_count=gdelt_count,
                arxiv_count=0,
                aiid_count=0,
                total_fetched=len(day_articles),
                passed_filter=len(passed_articles),
                extracted_incidents=len(day_extracted)
            )
        except Exception:
            pass
            
        time.sleep(1)
        
    print("\n" + "=" * 85)
    print(f"7-DAY BACKFILL COMPLETE: Added total of {total_added} new historical incidents to dataset!")
    print("=" * 85)

if __name__ == "__main__":
    run_7day_backfill()
