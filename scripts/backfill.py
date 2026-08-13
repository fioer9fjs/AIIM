"""
Historical 7-Day Backfill Pipeline for Global AI Incident Monitor.
Loops day-by-day through the past 7 days, fetches candidate news items,
decodes Google News RSS wrapper URLs using googlenewsdecoder, scrapes full text,
extracts taxonomy via Gemini 3.6 Flash, and syncs both incidents.json & Supabase PostgreSQL.
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
    """Decodes Google News RSS wrapper link to target publisher URL and scrapes full text paragraphs."""
    if not url or not HAS_SCRAPER:
        return ""
        
    real_url = url
    try:
        if "news.google.com" in url:
            decoded = gnewsdecoder(url)
            if isinstance(decoded, dict) and decoded.get("status") and decoded.get("decoded_url"):
                real_url = decoded.get("decoded_url")
    except Exception as e:
        print(f"Decoder note for {url[:40]}: {e}")
        
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        resp = requests.get(real_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
                tag.extract()
            paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 35]
            full_text = "\n\n".join(paragraphs)
            return full_text if len(full_text) > 100 else ""
    except Exception as e:
        print(f"Scraping error for {real_url[:50]}: {e}")
        
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
                
            # Enforce target backfill publication date
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
                    "description": description
                })
    except Exception:
        pass
    return articles

def update_knowledge_graph_edges(all_incidents: List[Dict[str, Any]]):
    data_dir = os.path.join(os.path.dirname(__file__), "..", "src", "data")
    edges_path = os.path.join(data_dir, "edges.json")
    
    existing_edges = []
    if os.path.exists(edges_path):
        try:
            with open(edges_path, "r", encoding="utf-8") as f:
                existing_edges = json.load(f)
        except Exception:
            existing_edges = []
            
    existing_pairs = set((e.get("source_id"), e.get("target_id")) for e in existing_edges)
    
    new_edges = []
    for i, inc1 in enumerate(all_incidents):
        parties1 = set(inc1.get("affected_parties", []))
        id1 = inc1.get("incident_id")
        
        for inc2 in all_incidents[i+1:]:
            id2 = inc2.get("incident_id")
            if not id1 or not id2 or id1 == id2:
                continue
                
            parties2 = set(inc2.get("affected_parties", []))
            common_parties = parties1.intersection(parties2)
            
            if common_parties and (inc1.get("root_cause_category") == inc2.get("root_cause_category") or inc1.get("harm_domain") == inc2.get("harm_domain")):
                if (id1, id2) not in existing_pairs and (id2, id1) not in existing_pairs:
                    rel_type = "lawsuit" if "lawsuit" in inc1.get("title", "").lower() or "lawsuit" in inc2.get("title", "").lower() else "related_cause"
                    edge_obj = {
                        "edge_id": f"EDGE-{len(existing_edges) + len(new_edges) + 1:03d}",
                        "source_id": id1,
                        "target_id": id2,
                        "relation_type": rel_type,
                        "description": f"Linked via shared entity ({', '.join(list(common_parties)[:2])}) & harm profile.",
                        "confidence": 0.90
                    }
                    new_edges.append(edge_obj)
                    existing_pairs.add((id1, id2))
                    
                    if id2 not in inc1.get("related_incidents", []):
                        inc1.setdefault("related_incidents", []).append(id2)
                    if id1 not in inc2.get("related_incidents", []):
                        inc2.setdefault("related_incidents", []).append(id1)

    if new_edges:
        existing_edges.extend(new_edges)
        with open(edges_path, "w", encoding="utf-8") as f:
            json.dump(existing_edges, f, indent=2)
        print(f"Updated Knowledge Graph: Added {len(new_edges)} new edges to src/data/edges.json!")

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
        update_knowledge_graph_edges(existing)
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
            inc = process_article_with_gemini(art, api_key, date_str)
            if inc and inc.get("is_ai_incident"):
                day_extracted.append(inc)
                print(f"     [FULL-TEXT EXTRACTED] {inc.get('title')} | Text Length: {len(inc.get('full_text', ''))} chars")
                
        added = save_to_incidents_json(day_extracted)
        total_added += added
        print(f"     Saved {added} new incidents for {date_str}.")
        time.sleep(1)
        
    print("\n" + "=" * 85)
    print(f"7-DAY BACKFILL COMPLETE: Added total of {total_added} new historical incidents to dataset!")
    print("=" * 85)

if __name__ == "__main__":
    run_7day_backfill()
