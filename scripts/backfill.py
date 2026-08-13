"""
Historical 7-Day Backfill Pipeline for Global AI Incident Monitor.
Loops day-by-day through the past 7 days, fetches raw candidate news items across sources,
scrapes full text, extracts taxonomy via Gemini 3.6 Flash, deduplicates, and populates incidents.json.
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
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    try:
        import google.generativeai as legacy_genai
        HAS_LEGACY_GENAI = True
    except ImportError:
        pass

from taxonomy_filters import (
    TIER_1_MODELS_PRODUCTS,
    TIER_1_PROVIDERS,
    TIER_1_INCIDENT_TERMS,
    score_article_relevance
)

SYSTEM_PROMPT = """
You are an expert AI Safety & Regulatory Incident Analyst.
Analyze the following news text about an AI-related event and extract structured taxonomy metadata.

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
  "root_cause_category": "data" | "model" | "human" | "governance" | "external" | "undetermined",
  "root_cause_subtype": "hallucination/poisoning/bias/adversarial_attack/etc",
  "failure_mode": "Brief narrative connecting cause to consequence based on full text details",
  "harm_domain": "persons_physical" | "persons_mental" | "persons_rights" | "property" | "environment" | "systemic_integrity" | "societal",
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
    if not url or not HAS_BS4:
        return ""
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.extract()
            paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 35]
            full_text = "\n\n".join(paragraphs)
            return full_text if len(full_text) > 100 else ""
    except Exception:
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
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={"response_mime_type": "application/json"}
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
            if full_text:
                data["full_text"] = full_text[:4000]
            return data
    except Exception:
        pass
        
    return None

def fetch_rss_for_date_range(query: str, target_date_str: str) -> List[Dict[str, Any]]:
    """Fetch RSS articles filtered for a specific date string (YYYY-MM-DD)."""
    # Combine query with Google date filter
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
                    "description": description
                })
    except Exception:
        pass
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
            inc["incident_id"] = f"INC-{datetime.now().strftime('%Y%m%d')}-{len(existing) + added_count + 1:03d}"
            if "related_incidents" not in inc:
                inc["related_incidents"] = []
            existing.insert(0, inc)
            existing_titles.add(title.lower())
            added_count += 1
            
    if added_count > 0:
        with open(incidents_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
            
    return added_count

def run_7day_backfill():
    print("=" * 85)
    print("GLOBAL AI INCIDENT MONITOR - 7-DAY HISTORICAL BACKFILL PIPELINE")
    print("=" * 85)
    
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("GEMINI_API_KEY environment variable not set. Please set key to run backfill.")
        return
        
    queries = [
        f'({ " OR ".join(TIER_1_MODELS_PRODUCTS[:6]) }) ({ " OR ".join(TIER_1_INCIDENT_TERMS[:6]) })',
        f'("AI incident" OR "LLM vulnerability" OR "deepfake fraud" OR "robotaxi accident")',
        f'("EU AI Act violation" OR "GDPR AI fine" OR "AI copyright lawsuit")'
    ]
    
    total_added = 0
    today = datetime.now()
    
    # Loop day by day for past 7 days
    for day_offset in range(1, 8):
        target_date = today - timedelta(days=day_offset)
        date_str = target_date.strftime("%Y-%m-%d")
        print(f"\n---> PROCESSING HISTORICAL DAY: {date_str} (Day -{day_offset})")
        
        day_articles = []
        for q in queries:
            arts = fetch_rss_for_date_range(q, date_str)
            day_articles.extend(arts)
            
        passed_articles = [a for a in day_articles if score_article_relevance(a['title'], a.get('description', '')) >= 0.4]
        print(f"     Fetched {len(day_articles)} raw news items -> {len(passed_articles)} passed relevance filter.")
        
        day_extracted = []
        for art in passed_articles:
            inc = process_article_with_gemini(art, api_key)
            if inc and inc.get("is_ai_incident"):
                inc["date"] = date_str # Ensure target backfill date
                day_extracted.append(inc)
                print(f"     [EXTRACTED] {inc.get('title')} [{inc.get('severity')}]")
                
        added = save_to_incidents_json(day_extracted)
        total_added += added
        print(f"     Saved {added} new incidents for {date_str}.")
        time.sleep(1) # Polite pause between days
        
    print("\n" + "=" * 85)
    print(f"7-DAY BACKFILL COMPLETE: Added total of {total_added} new historical incidents to dataset!")
    print("=" * 85)

if __name__ == "__main__":
    run_7day_backfill()
