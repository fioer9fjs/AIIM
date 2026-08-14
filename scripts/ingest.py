"""
Automated Data Ingestion & Full-Text Extraction Pipeline for Global AI Incident Monitor.
Dual GDELT Harvester (BigQuery + Rate-Protected API) & Google News RSS Decoder.
Scrapes complete article full texts, enforces publication date windowing, and syncs to Supabase.
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
  "financial_damage_usd": 15000000,
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

def process_article_with_gemini(article: Dict[str, str], api_key: str) -> Optional[Dict[str, Any]]:
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
                
            article_pub_date = article.get("pub_date_clean") or datetime.now().strftime("%Y-%m-%d")
            extracted_date = data.get("date", "")
            if not extracted_date or extracted_date.startswith("2023") or extracted_date.startswith("2024"):
                data["date"] = article_pub_date
                
            return data
    except Exception:
        pass
        
    return None

def fetch_google_news(query: str, max_items: int = 4) -> List[Dict[str, Any]]:
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    articles = []
    try:
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            for item in root.findall('./channel/item')[:max_items]:
                title = item.find('title').text if item.find('title') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                description = item.find('description').text if item.find('description') is not None else ""
                
                pub_date_clean = datetime.now().strftime("%Y-%m-%d")
                if pub_date:
                    try:
                        dt = datetime.strptime(pub_date[:16], "%a, %d %b %Y")
                        pub_date_clean = dt.strftime("%Y-%m-%d")
                    except Exception:
                        pass
                
                articles.append({
                    "title": title,
                    "link": link,
                    "pub_date": pub_date,
                    "pub_date_clean": pub_date_clean,
                    "description": description,
                    "source_type": "google_news_rss"
                })
    except Exception:
        pass
    return articles

def fetch_gdelt_bigquery(max_items: int = 15) -> List[Dict[str, Any]]:
    """Queries GDELT 2.0 Global Knowledge Graph via Google Cloud BigQuery public dataset."""
    if not HAS_BIGQUERY:
        return []
        
    articles = []
    try:
        project_id = os.environ.get("GCP_PROJECT_ID")
        client = bigquery.Client(project=project_id) if project_id else bigquery.Client()
        sql = f"""
        SELECT 
            DocumentIdentifier as link,
            SourceCommonName as domain,
            DATE(_PARTITIONDATE) as date
        FROM `gdelt-bq.gdeltv2.gkg_partitioned`
        WHERE _PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
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
                "pub_date": str(row.date),
                "pub_date_clean": str(row.date),
                "description": f"GDELT BigQuery event from {row.domain}",
                "source_type": "gdelt"
            })
        print(f"--> BigQuery GDELT Harvester successfully fetched {len(articles)} articles!")
    except Exception as e:
        print(f"BigQuery GDELT Harvester note: {e}")
    return articles

def fetch_gdelt_api(query: str, max_items: int = 3) -> List[Dict[str, Any]]:
    """Fetches news items from GDELT 2.0 REST API with rate-limit retry handling."""
    encoded_query = urllib.parse.quote(query)
    gdelt_url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={encoded_query}&mode=ArtList&maxrecords={max_items}&format=json&sort=date"
    articles = []
    
    for attempt in range(2):
        try:
            req = urllib.request.Request(gdelt_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                for art in data.get('articles', []):
                    seendate = art.get("seendate", "")
                    pub_date_clean = datetime.now().strftime("%Y-%m-%d")
                    if len(seendate) >= 8:
                        pub_date_clean = f"{seendate[:4]}-{seendate[4:6]}-{seendate[6:8]}"
                    articles.append({
                        "title": art.get("title", ""),
                        "link": art.get("url", ""),
                        "pub_date": seendate,
                        "pub_date_clean": pub_date_clean,
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

def save_to_incidents_json(new_incidents: List[Dict[str, Any]]):
    if not new_incidents:
        return
        
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
        print(f"Saved {added_count} new incidents to incidents.json.")
        
        try:
            from migrate_json_to_supabase import run_migration
            run_migration()
        except Exception as e:
            print(f"Note on Supabase sync: {e}")

def run_ingestion():
    print("Starting Multi-Source AI Incident Ingestion (BigQuery GDELT + Google News RSS)...")
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    from taxonomy_filters import (
        TIER_1_MODELS_PRODUCTS,
        TIER_1_PROVIDERS,
        TIER_1_INCIDENT_TERMS,
        score_article_relevance
    )

    queries = [
        f'({ " OR ".join(TIER_1_MODELS_PRODUCTS[:6]) }) ({ " OR ".join(TIER_1_INCIDENT_TERMS[:6]) })',
        f'("AI incident" OR "LLM vulnerability" OR "deepfake fraud")',
        f'("EU AI Act violation" OR "GDPR AI fine" OR "AI copyright lawsuit")'
    ]
    
    all_articles = []
    rss_count = 0
    gdelt_count = 0
    
    # 1. Try BigQuery GDELT
    bq_arts = fetch_gdelt_bigquery()
    if bq_arts:
        gdelt_count += len(bq_arts)
        all_articles.extend(bq_arts)
        
    # 2. Fetch Google News RSS & GDELT API fallback
    for q in queries:
        rss_arts = fetch_google_news(q)
        rss_count += len(rss_arts)
        all_articles.extend(rss_arts)
        
        if not bq_arts:
            gdelt_api_arts = fetch_gdelt_api(q)
            gdelt_count += len(gdelt_api_arts)
            all_articles.extend(gdelt_api_arts)
            time.sleep(1) # Rate limit protection
            
    passed_articles = [a for a in all_articles if score_article_relevance(a['title'], a.get('description', '')) >= 0.4]
    print(f"Harvester fetched {len(all_articles)} items (Google News RSS: {rss_count}, GDELT: {gdelt_count}) -> {len(passed_articles)} passed relevance filter.")
    
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return
        
    extracted_incidents = []
    for art in passed_articles:
        inc = process_article_with_gemini(art, api_key)
        if inc and inc.get("is_ai_incident"):
            extracted_incidents.append(inc)
            print(f"[EXTRACTED - {inc.get('source_type')}] {inc.get('title')} | Severity: {inc.get('severity')}")
            
    print(f"Ingestion complete. Extracted {len(extracted_incidents)} valid AI incidents.")
    save_to_incidents_json(extracted_incidents)
    
    try:
        from migrate_json_to_supabase import record_daily_source_stats
        record_daily_source_stats(
            stat_date=today_str,
            rss_count=rss_count,
            gdelt_count=gdelt_count,
            arxiv_count=0,
            aiid_count=0,
            total_fetched=len(all_articles),
            passed_filter=len(passed_articles),
            extracted_incidents=len(extracted_incidents)
        )
    except Exception:
        pass

if __name__ == "__main__":
    run_ingestion()
