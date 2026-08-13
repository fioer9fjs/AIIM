"""
Automated Data Ingestion & Extraction Pipeline for Global AI Incident Monitor.
Fetches GDELT and Google News RSS feeds, extracts academic/regulatory taxonomy using
the official Google GenAI SDK (Gemini 2.5 Flash), detects deduplications/timeline links,
and updates the incident store.
"""

import os
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any, Optional

# Prefer official google-genai SDK, fallback to google-generativeai if needed
HAS_GENAI = False
HAS_LEGACY_GENAI = False

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    try:
        import google.generativeai as legacy_genai
        HAS_LEGACY_GENAI = True
    except ImportError:
        pass

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
  "failure_mode": "Brief narrative connecting cause to consequence",
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

SEARCH_QUERIES = [
    "AI incident OR AI safety risk",
    "LLM vulnerability OR prompt injection",
    "AI lawsuit OR copyright AI",
    "deepfake fraud OR AI scam",
    "autonomous vehicle accident OR robotaxi"
]

def fetch_google_news_rss(query: str) -> List[Dict[str, str]]:
    """Fetch recent news articles from Google News RSS feed."""
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    articles = []
    try:
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            for item in root.findall('./channel/item')[:5]: # Top 5 per query
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
    except Exception as e:
        print(f"Error fetching Google News RSS for '{query}': {e}")
        
    return articles

def process_article_with_gemini(article: Dict[str, str], api_key: str) -> Optional[Dict[str, Any]]:
    """Process news text with Gemini Flash using official google-genai SDK."""
    if not api_key:
        print("Missing Gemini API Key.")
        return None
        
    prompt = f"{SYSTEM_PROMPT}\n\nARTICLE TITLE: {article['title']}\nARTICLE CONTENT: {article['description']}"
    
    text_clean = ""
    
    if HAS_GENAI:
        try:
            client = genai.Client(api_key=api_key)
            # Try gemini-2.5-flash first, fallback to gemini-1.5-flash
            for model_name in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"]:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config={"response_mime_type": "application/json"}
                    )
                    text_clean = response.text.strip()
                    break
                except Exception as inner_e:
                    print(f"Model {model_name} failed: {inner_e}")
                    continue
        except Exception as e:
            print(f"google-genai Client error: {e}")
            
    elif HAS_LEGACY_GENAI:
        try:
            legacy_genai.configure(api_key=api_key)
            for model_name in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-pro"]:
                try:
                    model = legacy_genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                    text_clean = response.text.strip()
                    break
                except Exception:
                    continue
        except Exception as e:
            print(f"Legacy Gemini API error: {e}")

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
            return data
    except Exception as e:
        print(f"JSON parsing error: {e}")
        
    return None

def save_to_incidents_json(new_incidents: List[Dict[str, Any]]):
    """Save/merge new incidents into src/data/incidents.json."""
    if not new_incidents:
        print("No new valid AI incidents extracted to save.")
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
            inc["incident_id"] = f"INC-{datetime.now().strftime('%Y%m%d')}-{len(existing) + added_count + 1:03d}"
            if "related_incidents" not in inc:
                inc["related_incidents"] = []
            existing.insert(0, inc) # Add newest to top
            existing_titles.add(title.lower())
            added_count += 1
            
    if added_count > 0:
        with open(incidents_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        print(f"Successfully saved {added_count} new live incidents to src/data/incidents.json!")
    else:
        print("All extracted incidents were duplicates of existing entries.")

def run_ingestion():
    print("Starting automated AI Incident Ingestion pipeline...")
    all_articles = []
    for q in SEARCH_QUERIES:
        arts = fetch_google_news_rss(q)
        all_articles.extend(arts)
        
    print(f"Fetched total of {len(all_articles)} candidate news items across queries.")
    
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("GEMINI_API_KEY environment variable not set. Running in dry-run mode.")
        for i, a in enumerate(all_articles[:3], 1):
            print(f"[{i}] {a['title']} ({a['pub_date']})")
        return
        
    extracted_incidents = []
    for art in all_articles:
        inc = process_article_with_gemini(art, api_key)
        if inc and inc.get("is_ai_incident"):
            extracted_incidents.append(inc)
            print(f"[EXTRACTED] {inc.get('title')} | Severity: {inc.get('severity')} | Harm: {inc.get('harm_domain')}")
            
    print(f"Ingestion complete. Extracted {len(extracted_incidents)} valid AI incidents.")
    save_to_incidents_json(extracted_incidents)

if __name__ == "__main__":
    run_ingestion()
