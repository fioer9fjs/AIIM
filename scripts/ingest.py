"""
Automated Data Ingestion & Full-Text Extraction Pipeline for Global AI Incident Monitor.
Harvests multi-tier queries, scrapes full text, applies noise exclusions, uses Gemini 3.6 Flash,
updates BOTH src/data/incidents.json AND src/data/edges.json synchronously for Knowledge Graph edges.
"""

import os
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
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
    if not url or not HAS_BS4:
        return ""
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.extract()
            paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 35]
            full_text = "\n\n".join(paragraphs)
            return full_text if len(full_text) > 100 else ""
    except Exception:
        return ""

def get_candidate_models(api_key: str) -> List[str]:
    candidates = list(PREFERRED_MODELS)
    if HAS_GENAI:
        try:
            client = genai.Client(api_key=api_key)
            fetched = [m.name.replace("models/", "") for m in client.models.list()]
            if fetched:
                for f in fetched:
                    if f not in candidates:
                        candidates.append(f)
        except Exception:
            pass
    return candidates

def process_article_with_gemini(article: Dict[str, str], api_key: str) -> Optional[Dict[str, Any]]:
    global _WORKING_MODEL_NAME
    if not api_key:
        return None
        
    full_text = fetch_full_text(article['link'])
    text_payload = full_text if full_text else article.get('description', '')
    prompt = f"{SYSTEM_PROMPT}\n\nARTICLE TITLE: {article['title']}\n\nARTICLE FULL TEXT:\n{text_payload[:12000]}"
    
    candidate_models = get_candidate_models(api_key)
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
                    if _WORKING_MODEL_NAME != model_name:
                        _WORKING_MODEL_NAME = model_name
                        print(f"--> Verified working Gemini model: {model_name}")
                    break
            except Exception:
                continue
                    
        elif HAS_LEGACY_GENAI:
            try:
                legacy_genai.configure(api_key=api_key)
                model = legacy_genai.GenerativeModel(model_name)
                response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
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
    except Exception as e:
        print(f"JSON parsing error: {e}")
        
    return None

def update_knowledge_graph_edges(all_incidents: List[Dict[str, Any]]):
    """Automatically constructs and updates Knowledge Graph edges based on shared entities and incident evolution."""
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
    # Discover connections between incidents sharing affected parties & root cause category
    for i, inc1 in enumerate(all_incidents):
        parties1 = set(inc1.get("affected_parties", []))
        id1 = inc1.get("incident_id")
        
        for inc2 in all_incidents[i+1:]:
            id2 = inc2.get("incident_id")
            if not id1 or not id2 or id1 == id2:
                continue
                
            parties2 = set(inc2.get("affected_parties", []))
            common_parties = parties1.intersection(parties2)
            
            # If they share an affected company/entity and root cause or harm domain
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
                    
                    # Update related_incidents list in incident objects
                    if id2 not in inc1.get("related_incidents", []):
                        inc1.setdefault("related_incidents", []).append(id2)
                    if id1 not in inc2.get("related_incidents", []):
                        inc2.setdefault("related_incidents", []).append(id1)

    if new_edges:
        existing_edges.extend(new_edges)
        with open(edges_path, "w", encoding="utf-8") as f:
            json.dump(existing_edges, f, indent=2)
        print(f"Updated Knowledge Graph: Added {len(new_edges)} new edges to src/data/edges.json!")

def save_to_incidents_json(new_incidents: List[Dict[str, Any]]):
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
            existing.insert(0, inc)
            existing_titles.add(title.lower())
            added_count += 1
            
    if added_count > 0 or existing:
        # Synchronously update Knowledge Graph edges
        update_knowledge_graph_edges(existing)
        
        with open(incidents_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        print(f"Successfully saved {added_count} new incidents and updated edges.json!")

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
                
                articles.append({
                    "title": title,
                    "link": link,
                    "pub_date": pub_date,
                    "description": description
                })
    except Exception as e:
        print(f"Error fetching RSS: {e}")
    return articles

def run_ingestion():
    print("Starting Full-Text AI Incident & Knowledge Graph Ingestion pipeline...")
    
    from taxonomy_filters import (
        TIER_1_MODELS_PRODUCTS,
        TIER_1_PROVIDERS,
        TIER_1_INCIDENT_TERMS,
        score_article_relevance
    )

    queries = [
        f'({ " OR ".join(TIER_1_MODELS_PRODUCTS[:8]) }) ({ " OR ".join(TIER_1_INCIDENT_TERMS[:8]) })',
        f'({ " OR ".join(TIER_1_PROVIDERS[:8]) }) ({ " OR ".join(TIER_1_INCIDENT_TERMS[8:16]) })',
        f'("AI incident" OR "LLM vulnerability" OR "deepfake fraud" OR "robotaxi accident")',
        f'("EU AI Act violation" OR "GDPR AI fine" OR "AI copyright lawsuit")'
    ]
    
    all_articles = []
    for q in queries:
        arts = fetch_google_news(q)
        all_articles.extend(arts)
        
    passed_articles = []
    for art in all_articles:
        score = score_article_relevance(art['title'], art.get('description', ''))
        if score >= 0.4:
            passed_articles.append(art)
            
    print(f"Harvester fetched {len(all_articles)} items -> {len(passed_articles)} passed Tier 1/2 relevance filter.")
    
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("GEMINI_API_KEY environment variable not set. Running in dry-run mode.")
        return
        
    extracted_incidents = []
    for art in passed_articles:
        inc = process_article_with_gemini(art, api_key)
        if inc and inc.get("is_ai_incident"):
            extracted_incidents.append(inc)
            print(f"[FULL-TEXT EXTRACTED] {inc.get('title')} | Severity: {inc.get('severity')}")
            
    print(f"Ingestion complete. Extracted {len(extracted_incidents)} valid AI incidents.")
    save_to_incidents_json(extracted_incidents)

if __name__ == "__main__":
    run_ingestion()
