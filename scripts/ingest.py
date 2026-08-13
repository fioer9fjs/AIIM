"""
Automated Data Ingestion & Extraction Pipeline for Global AI Incident Monitor.
Fetches GDELT and Google News RSS feeds, extracts academic/regulatory taxonomy using
Gemini Flash, detects deduplications/timeline links, and updates the incident store.
"""

import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# Prompt instruction template enforcing structured taxonomy output
SYSTEM_PROMPT = """
You are an expert AI Safety & Regulatory Incident Analyst.
Analyze the following news text about an AI-related event and extract structured taxonomy metadata.

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
    "verification_status": 0.0-1.0,
    "lifecycle_phase": 0.0-1.0,
    "system_classification": 0.0-1.0,
    "root_cause_category": 0.0-1.0,
    "harm_domain": 0.0-1.0,
    "severity": 0.0-1.0
  },
  "geographic_scope": ["Country/Region"],
  "affected_parties": ["Entity1", "Entity2"]
}
"""

def fetch_google_news_rss(query: str = "AI incident OR LLM security leak OR AI glitch") -> List[Dict[str, str]]:
    """Fetch recent news articles from Google News RSS feed."""
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    articles = []
    try:
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            for item in root.findall('./channel/item')[:10]: # Top 10 items
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
        print(f"Error fetching Google News RSS: {e}")
        
    return articles

def process_article_with_gemini(article: Dict[str, str], api_key: str) -> Optional[Dict[str, Any]]:
    """Process news text with Gemini Flash to extract taxonomy."""
    if not HAS_GEMINI or not api_key:
        print("Gemini SDK not configured or missing API key.")
        return None
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"{SYSTEM_PROMPT}\n\nARTICLE TITLE: {article['title']}\nARTICLE CONTENT: {article['description']}"
    
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        data = json.loads(response.text)
        if data.get("is_ai_incident"):
            data["source_urls"] = [article["link"]]
            return data
    except Exception as e:
        print(f"Gemini API error during extraction: {e}")
        
    return None

def run_ingestion():
    print("Starting automated AI Incident Ingestion pipeline...")
    articles = fetch_google_news_rss()
    print(f"Fetched {len(articles)} candidate news items.")
    
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("GEMINI_API_KEY environment variable not set. Running in dry-run/feed verification mode.")
        for i, a in enumerate(articles[:3], 1):
            print(f"[{i}] {a['title']} ({a['pub_date']})")
        return
        
    extracted_incidents = []
    for art in articles:
        inc = process_article_with_gemini(art, api_key)
        if inc:
            extracted_incidents.append(inc)
            print(f"Extracted Incident: {inc['title']} [Severity: {inc['severity']}]")
            
    print(f"Ingestion complete. Extracted {len(extracted_incidents)} valid AI incidents.")

if __name__ == "__main__":
    run_ingestion()
