"""
Multi-Source Data Harvester for Global AI Incident Monitor.
Uses 3-Tier Keyword Taxonomy & Exclusion Rules (Aviation/Financial noise filters).
Harvests candidate incidents across:
1. GDELT Project (BigQuery & Doc API v2)
2. AI Incident Database (AIID API)
3. ArXiv AI Safety & Security Papers
4. Google News Global Feeds with Tier 1 query combinations
"""

import sys
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

from taxonomy_filters import (
    TIER_1_CORE_TERMS,
    TIER_1_MODELS_PRODUCTS,
    TIER_1_PROVIDERS,
    TIER_1_INCIDENT_TERMS,
    TIER_2_HARMS_AND_REGULATORY,
    EXCLUSIONS_AVIATION,
    EXCLUSIONS_FINANCIAL,
    score_article_relevance,
    build_gdelt_sql_query
)

# Ensure UTF-8 console output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Generate high-precision Tier 1 query combinations
TIER_1_QUERIES = [
    f'({ " OR ".join(TIER_1_MODELS_PRODUCTS[:8]) }) ({ " OR ".join(TIER_1_INCIDENT_TERMS[:8]) })',
    f'({ " OR ".join(TIER_1_PROVIDERS[:8]) }) ({ " OR ".join(TIER_1_INCIDENT_TERMS[8:16]) })',
    f'("AI incident" OR "LLM vulnerability" OR "deepfake fraud" OR "robotaxi accident")',
    f'("EU AI Act violation" OR "GDPR AI fine" OR "AI copyright lawsuit")'
]

def fetch_aiid_database(max_items: int = 5) -> List[Dict[str, Any]]:
    """Fetch recent incidents from the official AI Incident Database (AIID) API."""
    articles = []
    try:
        req = urllib.request.Request(
            "https://incidentdatabase.ai/api/incidents",
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            for inc in data[:max_items]:
                articles.append({
                    "title": inc.get('title', ''),
                    "link": f"https://incidentdatabase.ai/cite/{inc.get('incident_id')}",
                    "pub_date": inc.get('date', ''),
                    "summary": inc.get('description', '')[:150] + '...'
                })
    except Exception as e:
        print(f"  [Note on AIID fetch: {e}]", flush=True)
    return articles

def fetch_arxiv_ai_safety(max_items: int = 5) -> List[Dict[str, Any]]:
    """Fetch recent research papers on AI security, vulnerabilities, and jailbreaks from ArXiv API."""
    url = "http://export.arxiv.org/api/query?search_query=cat:cs.CR+AND+all:%22jailbreak%22+OR+all:%22prompt+injection%22+OR+all:%22LLM+vulnerability%22&max_results=5&sortBy=submittedDate&sortOrder=descending"
    articles = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall('atom:entry', ns)[:max_items]:
                title = entry.find('atom:title', ns).text.strip().replace('\n', ' ') if entry.find('atom:title', ns) is not None else ""
                link = entry.find('atom:id', ns).text if entry.find('atom:id', ns) is not None else ""
                published = entry.find('atom:published', ns).text[:10] if entry.find('atom:published', ns) is not None else ""
                summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')[:150] if entry.find('atom:summary', ns) is not None else ""
                
                articles.append({
                    "title": f"[ArXiv Paper] {title}",
                    "link": link,
                    "pub_date": published,
                    "summary": summary + '...'
                })
    except Exception as e:
        print(f"  [Error fetching ArXiv: {e}]", flush=True)
    return articles

def fetch_gdelt_doc_api(query: str = '"artificial intelligence" (incident OR harm OR lawsuit OR leak)', max_items: int = 5) -> List[Dict[str, Any]]:
    """Fetch global incidents from GDELT Doc 2.0 API with Tier 1 query and Exclusion filters."""
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={encoded_query}&mode=artlist&maxrecords={max_items}&format=json"
    articles = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            for art in data.get('articles', []):
                articles.append({
                    "title": art.get('title', ''),
                    "link": art.get('url', ''),
                    "pub_date": art.get('seendate', ''),
                    "summary": f"GDELT Domain: {art.get('domain', 'global news')}"
                })
    except Exception as e:
        print(f"  [Note on GDELT fetch: {e}]", flush=True)
    return articles

def fetch_google_news(query: str, max_items: int = 5) -> List[Dict[str, Any]]:
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
                
                articles.append({
                    "title": title,
                    "link": link,
                    "pub_date": pub_date,
                    "summary": "Google News Tier 1 Feed"
                })
    except Exception as e:
        print(f"  [Error fetching RSS: {e}]", flush=True)
    return articles

def inspect_all_sources():
    print("=" * 85, flush=True)
    print("TIERED MULTI-SOURCE HARVESTER (WITH NOISE EXCLUSIONS & BIGQUERY SQL)", flush=True)
    print("=" * 85, flush=True)
    
    print("\n[Generated BigQuery GDELT SQL Query (Tier 1 + Exclusions)]:")
    print(build_gdelt_sql_query())
    print("-" * 85, flush=True)

    sources = [
        ("AI Incident Database (AIID API)", fetch_aiid_database()),
        ("ArXiv AI Safety & Vulnerability Papers", fetch_arxiv_ai_safety()),
        ("GDELT 2.0 Global Knowledge Graph API", fetch_gdelt_doc_api()),
    ]
    
    for idx, q in enumerate(TIER_1_QUERIES, 1):
        sources.append((f"Google News Tier 1 Combination #{idx}", fetch_google_news(q)))

    total_articles = 0
    passed_articles = 0

    for name, items in sources:
        print(f"\n---> SOURCE: {name}", flush=True)
        print(f"     Retrieved {len(items)} candidate records:", flush=True)
        for idx, item in enumerate(items, 1):
            score = score_article_relevance(item['title'], item.get('summary', ''))
            status = "PASSED FILTER" if score >= 0.4 else "EXCLUDED (Noise/Irrelevant)"
            
            clean_title = item['title'].encode('ascii', 'ignore').decode('ascii')
            print(f"     [{idx}] [{status} | Score: {score:.1f}] {clean_title}", flush=True)
            print(f"         URL:   {item['link']}", flush=True)
            print(f"         Date:  {item['pub_date']}", flush=True)
            
            if score >= 0.4:
                passed_articles += 1
            total_articles += 1

    print("\n" + "=" * 85, flush=True)
    print(f"TIERED HARVEST SUMMARY: {passed_articles} high-relevance passed items out of {total_articles} candidate items from {len(sources)} sources", flush=True)
    print("=" * 85, flush=True)

if __name__ == "__main__":
    inspect_all_sources()
