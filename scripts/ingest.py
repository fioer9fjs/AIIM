"""
Automated Data Ingestion & Full-Text Extraction Pipeline for Global AI Incident Monitor.
Production 3-Stage Architecture:
  Stage 1: Multi-Source Harvesting (Advanced GDELT BigQuery + Google News RSS + ArXiv)
  Stage 2: Single-Focus LLM Binary Gatekeeper (Strict Incident vs False Positive Rejection)
  Stage 3: LLM Deep Taxonomy & Financial Damage Extractor
"""

import os
import json
import time
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from scripts.clean_and_enrich_incidents import estimate_financial_damage, assign_compliance_frameworks, assign_impact_scope

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
    HAS_GENAI = False

try:
    from google.cloud import bigquery
    HAS_BIGQUERY = True
except ImportError:
    HAS_BIGQUERY = False

PREFERRED_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest"
]

_WORKING_MODEL_NAME = None

# STAGE 2 PROMPT: SINGLE-FOCUS BINARY GATEKEEPER
GATEKEEPER_PROMPT = """
You are a strict, single-purpose AI Incident Classification Gatekeeper.
Your ONLY TASK is to decide if the given news article describes a REAL-WORLD AI OPERATIONAL INCIDENT (is_ai_incident: true) or NOT (is_ai_incident: false).

DEFINITIONS:
1. AN "AI INCIDENT" (is_ai_incident = true) MUST BE:
   - A real-world operational event where an AI system/model/agent caused physical harm, property damage, mental harm, financial fraud/theft, privacy/biometric breach, cyberattack/sandbox escape, algorithmic discrimination in hiring/loans, or unauthorized autonomous actions.
   - A formal regulatory enforcement action or government ban against a specific AI deployment due to safety failures.

2. STRICT EXCLUSIONS (MUST RETURN is_ai_incident = false):
   - Securities class actions, shareholder lawsuits, or investor losses arising solely from stock price drops, quarterly earnings, or alleged management overstatement of AI revenue/Copilot adoption (e.g. Levi & Korsinsky, Robbins Geller, Pomerantz).
   - Routine commercial product announcements, model releases, software updates, or corporate PR marketing.
   - Speculative debate or academic papers discussing future artificial general intelligence (AGI) without a real-world event.

Return ONLY a valid JSON object:
{
  "is_ai_incident": true,
  "confidence": 0.95,
  "rejection_reason": ""
}
or
{
  "is_ai_incident": false,
  "confidence": 0.98,
  "rejection_reason": "Securities class action regarding stock price drop; no operational AI system failure or direct harm."
}
"""

# STAGE 3 PROMPT: DEEP TAXONOMY & FINANCIAL DAMAGE EXTRACTOR
TAXONOMY_PROMPT = """
You are an expert AI Safety & Regulatory Incident Analyst.
The provided article HAS BEEN CONFIRMED as a real-world AI incident. Extract structured taxonomy metadata.

Return ONLY a valid JSON object matching this exact schema:
{
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
  "impact_scope": "discrete_incident" | "cumulative_macro_trend", // MUST use "cumulative_macro_trend" if article describes aggregated statistics/totals over a period (e.g. TRM Labs H1 report, Chainalysis annual total, Interpol global losses, multi-hack theft totals); use "discrete_incident" ONLY for single specific events
  "financial_damage_usd": 15000000,
  "eu_ai_act_tier": "prohibited" | "high_risk" | "limited_risk" | "minimal_risk",
  "nist_ai_rmf_function": "GOVERN" | "MAP" | "MEASURE" | "MANAGE",
  "iso_42001_category": "Internal_Governance" | "Data_&_Resources" | "System_Impact" | "Operational_Security",
  "natsec_impact": true,
  "temporality": "actual" | "potential" | "latent",
  "severity": "critical" | "high" | "medium" | "low",
  "geographic_scope": ["United States"],
  "affected_parties": ["Organization A"],
  "confidence_scores": {
    "verification_status": 0.95,
    "severity": 0.90
  }
}
"""

def fetch_full_text_and_title(url: str) -> Dict[str, str]:
    """Scrapes full text body and HTML title from an article URL."""
    if not url or not HAS_SCRAPER:
        return {"title": "", "full_text": ""}
        
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
            html_title = soup.title.string.strip() if soup.title and soup.title.string else ""
            
            for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
                tag.extract()
            paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 35]
            full_text = "\n\n".join(paragraphs)
            return {
                "title": html_title,
                "full_text": full_text if len(full_text) > 100 else ""
            }
    except Exception:
        pass
        
    return {"title": "", "full_text": ""}

def stage2_binary_gatekeeper(title: str, text: str, api_key: str) -> Dict[str, Any]:
    """STAGE 2: Dedicated single-focus LLM Gatekeeper for Incident vs False Positive Rejection."""
    global _WORKING_MODEL_NAME
    if not api_key:
        return {"is_ai_incident": False, "confidence": 0.0, "rejection_reason": "No Gemini API Key provided"}

    prompt = f"{GATEKEEPER_PROMPT}\n\nARTICLE TITLE: {title}\n\nARTICLE TEXT:\n{text[:6000]}"
    
    candidate_models = list(PREFERRED_MODELS)
    if _WORKING_MODEL_NAME and _WORKING_MODEL_NAME in candidate_models:
        candidate_models.remove(_WORKING_MODEL_NAME)
        candidate_models.insert(0, _WORKING_MODEL_NAME)

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
                    if text_clean.startswith("```json"):
                        text_clean = text_clean[7:]
                    if text_clean.endswith("```"):
                        text_clean = text_clean[:-3]
                    data = json.loads(text_clean.strip())
                    _WORKING_MODEL_NAME = model_name
                    return {
                        "is_ai_incident": bool(data.get("is_ai_incident", False)),
                        "confidence": float(data.get("confidence", 0.9)),
                        "rejection_reason": str(data.get("rejection_reason", ""))
                    }
            except Exception:
                continue

    return {"is_ai_incident": False, "confidence": 0.0, "rejection_reason": "LLM Gatekeeper execution error"}

def stage3_extract_taxonomy(title: str, text: str, api_key: str) -> Optional[Dict[str, Any]]:
    """STAGE 3: Deep Taxonomy and Financial Damage Extractor (Invoked ONLY if Stage 2 Passed)."""
    global _WORKING_MODEL_NAME
    if not api_key:
        return None

    prompt = f"{TAXONOMY_PROMPT}\n\nARTICLE TITLE: {title}\n\nARTICLE FULL TEXT:\n{text[:12000]}"
    
    candidate_models = list(PREFERRED_MODELS)
    if _WORKING_MODEL_NAME and _WORKING_MODEL_NAME in candidate_models:
        candidate_models.remove(_WORKING_MODEL_NAME)
        candidate_models.insert(0, _WORKING_MODEL_NAME)

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
                    if text_clean.startswith("```json"):
                        text_clean = text_clean[7:]
                    if text_clean.endswith("```"):
                        text_clean = text_clean[:-3]
                    data = json.loads(text_clean.strip())
                    _WORKING_MODEL_NAME = model_name
                    return data
            except Exception:
                continue

    return None

def process_article_3stage_pipeline(article: Dict[str, str], api_key: str) -> Optional[Dict[str, Any]]:
    """Executes the full 3-Stage Ingestion Pipeline on a candidate article."""
    scraped = fetch_full_text_and_title(article['link'])
    real_title = scraped["title"] or article.get("title", "")
    real_text = scraped["full_text"] or article.get("description", "")
    
    if not real_title and not real_text:
        return None

    # STAGE 2: BINARY GATEKEEPER
    gatekeeper_result = stage2_binary_gatekeeper(real_title, real_text, api_key)
    if not gatekeeper_result.get("is_ai_incident"):
        print(f"  [STAGE 2 REJECTED] '{real_title[:45]}...' Reason: {gatekeeper_result.get('rejection_reason')}")
        return None

    # STAGE 3: DEEP TAXONOMY & FINANCIAL DAMAGE EXTRACTION
    data = stage3_extract_taxonomy(real_title, real_text, api_key)
    if not data:
        return None

    # AUTOMATIC FINANCIAL ENRICHMENT & IMPACT SCOPE VALIDATOR
    assign_compliance_frameworks(data)
    usd = data.get("financial_damage_usd", 0) or 0
    if usd <= 0:
        usd, methodology = estimate_financial_damage(data)
        data["financial_damage_usd"] = usd
        data["valuation_methodology"] = methodology
    else:
        data["valuation_methodology"] = "explicit_confirmed"
    assign_impact_scope(data)

    data["source_urls"] = [article["link"]]
    data["source_type"] = article.get("source_type", "google_news_rss")
    if real_text:
        data["full_text"] = real_text[:4000]
        
    article_pub_date = article.get("pub_date_clean") or datetime.now().strftime("%Y-%m-%d")
    extracted_date = data.get("date", "")
    if not extracted_date or extracted_date.startswith("2023") or extracted_date.startswith("2024"):
        data["date"] = article_pub_date
        
    print(f"  [STAGE 3 PASSED & ENRICHED] '{data.get('title')[:50]}...'")
    return data

def unwrap_google_news_link(url: str) -> str:
    if "news.google.com" not in url:
        return url
    try:
        from googlenewsdecoder import new_decoderv1
        res = new_decoderv1(url)
        if isinstance(res, dict) and res.get("status") and res.get("decoded_url"):
            decoded = res["decoded_url"]
            if "news.google.com" not in decoded:
                return decoded
    except Exception:
        pass
    return url

def fetch_google_news(query: str, max_items: int = 12) -> List[Dict[str, Any]]:
    """Fetches candidate articles from Google News RSS feed."""
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    articles = []
    try:
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            for item in root.findall('./channel/item')[:max_items]:
                raw_title = item.find('title').text if item.find('title') is not None else ""
                title = re.sub(r' - [^-]+$', '', raw_title) if raw_title else ""
                raw_link = item.find('link').text if item.find('link') is not None else ""
                link = unwrap_google_news_link(raw_link)
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

def fetch_gdelt_bigquery(max_items: int = 25) -> List[Dict[str, Any]]:
    """
    ADVANCED GDELT GKG HARVESTER VIA BIGQUERY:
      - Uses _PARTITIONTIME windowing for partition pruning
      - Filters CAST(SPLIT(V2Tone, ',')[OFFSET(0)] AS FLOAT64) < -0.5 for negative sentiment
      - Includes dry-run cost control safety check (< 50 GB scan)
      - Captures AllNames entity metadata
    """
    if not HAS_BIGQUERY:
        return []
        
    articles = []
    try:
        project_id = os.environ.get("GCP_PROJECT_ID") or os.environ.get("GCP_PROJECT")
        client = bigquery.Client(project=project_id) if project_id else bigquery.Client()
        
        sql = f"""
        SELECT 
            DocumentIdentifier as link,
            SourceCommonName as domain,
            CAST(SPLIT(V2Tone, ',')[OFFSET(0)] AS FLOAT64) as tone,
            V2Themes as themes,
            AllNames as names,
            DATE(_PARTITIONDATE) as date
        FROM `gdelt-bq.gdeltv2.gkg_partitioned`
        WHERE _PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
          AND REGEXP_CONTAINS(LOWER(V2Themes), r'(artificial_intelligence|machine_learning|autonomous_vehicles|robotics)')
          AND REGEXP_CONTAINS(LOWER(V2Themes), r'(cyber_attack|crime_hacking|security_breach|privacy|bias|lawsuit|investigation|accident|fatality|system_failure)')
          AND CAST(SPLIT(V2Tone, ',')[OFFSET(0)] AS FLOAT64) < -0.5
        LIMIT {max_items};
        """
        
        # Dry-run cost control safety check
        dry_job = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
        estimated_bytes = dry_job.total_bytes_processed
        print(f"[GDELT BigQuery Dry-Run] Estimated bytes scanned: {estimated_bytes / (1024**3):.3f} GB")
        if estimated_bytes > 50 * 1024 * 1024 * 1024:
            print("GDELT BigQuery query skipped: Exceeds 50 GB safety limit.")
            return []

        query_job = client.query(sql)
        for row in query_job.result():
            articles.append({
                "title": f"GDELT Event from {row.domain}",
                "link": row.link,
                "pub_date": str(row.date),
                "pub_date_clean": str(row.date),
                "description": f"GDELT GKG Event ({row.domain}) | Tone: {row.tone}",
                "source_type": "gdelt",
                "gdelt_names": str(row.names)[:500] if row.names else ""
            })
        print(f"--> Advanced GDELT BigQuery Harvester fetched {len(articles)} candidate articles.")
    except Exception as e:
        print(f"BigQuery GDELT Harvester note: {e}")
    return articles

def is_fuzzy_duplicate(inc1: Dict[str, Any], inc2: Dict[str, Any]) -> bool:
    import difflib
    t1 = inc1.get("title", "").lower()
    t2 = inc2.get("title", "").lower()
    ratio = difflib.SequenceMatcher(None, t1, t2).ratio()
    if ratio >= 0.55:
        return True
    words1 = set(inc1.get("summary", "").lower().split())
    words2 = set(inc2.get("summary", "").lower().split())
    jaccard = len(words1.intersection(words2)) / float(max(len(words1.union(words2)), 1))
    return jaccard >= 0.45

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
            
    added_count = 0
    for inc in new_incidents:
        if not any(is_fuzzy_duplicate(inc, item) for item in existing):
            if "incident_id" not in inc or not inc["incident_id"]:
                date_prefix = (inc.get("date") or datetime.now().strftime("%Y%m%d")).replace("-", "")
                seq_num = len(existing) + added_count + 1
                inc["incident_id"] = f"INC-{date_prefix}-{seq_num:03d}"
            existing.insert(0, inc)
            added_count += 1
            
    if added_count > 0:
        with open(incidents_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        print(f"\nSaved {added_count} new incidents to local JSON dataset: {incidents_path}")

def run_ingestion():
    load_env_file()
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("GEMINI_API_KEY environment variable missing.")
        return

    print("=" * 80)
    print("GLOBAL AI INCIDENT MONITOR - 3-STAGE INGESTION PIPELINE")
    print("=" * 80)

    # STAGE 1: MULTI-SOURCE HARVESTING
    print("\n---> STAGE 1: HARVESTING CANDIDATES (Google News + GDELT BigQuery)...")
    candidates = []
    
    query = '("AI" OR "Artificial Intelligence" OR "LLM" OR "ChatGPT" OR "Claude") AND ("incident" OR "breach" OR "malfunction" OR "lawsuit" OR "investigation" OR "vulnerability")'
    gnews_articles = fetch_google_news(query, max_items=12)
    candidates.extend(gnews_articles)
    print(f"Harvested {len(gnews_articles)} Google News candidate articles.")
    
    gdelt_bq_articles = fetch_gdelt_bigquery(max_items=15)
    candidates.extend(gdelt_bq_articles)
    
    print(f"Total Candidate Pool: {len(candidates)} articles.")

    # STAGE 2 & 3: GATEKEEPER & TAXONOMY EXTRACTION
    print("\n---> STAGE 2 & STAGE 3: RUNNING LLM GATEKEEPER & TAXONOMY EXTRACTION...")
    new_incidents = []
    for idx, candidate in enumerate(candidates, 1):
        print(f"\nProcessing [{idx}/{len(candidates)}]: '{candidate.get('title')[:55]}...'")
        result = process_article_3stage_pipeline(candidate, api_key)
        if result:
            new_incidents.append(result)

    print(f"\nIngestion Complete: {len(new_incidents)} validated incidents passed all 3 stages.")

    # SAVE LOCAL JSON & SYNC SUPABASE
    save_to_incidents_json(new_incidents)
    
    try:
        from migrate_json_to_supabase import run_migration
        run_migration()
    except Exception as e:
        print(f"Supabase sync note: {e}")

def load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

if __name__ == "__main__":
    run_ingestion()
