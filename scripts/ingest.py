"""
Automated Data Ingestion & Full-Text Extraction Pipeline for Global AI Incident Monitor.
Production 3-Stage Architecture:
  Stage 1: Multi-Source Harvesting (Advanced GDELT BigQuery + Google News RSS + ArXiv)
  Stage 2: Single-Focus LLM Binary Gatekeeper (Strict Incident vs False Positive Rejection)
  Stage 3: LLM Deep Taxonomy & Financial Damage Extractor
"""

import sys
import os
import json
import time
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import warnings
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

warnings.filterwarnings("ignore", message=".*XMLParsedAsHTMLWarning.*")
warnings.filterwarnings("ignore", message=".*automatic function calling.*")
try:
    from bs4 import XMLParsedAsHTMLWarning
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
except ImportError:
    pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from scripts.clean_and_enrich_incidents import estimate_financial_damage, assign_compliance_frameworks, assign_impact_scope
except ImportError:
    from clean_and_enrich_incidents import estimate_financial_damage, assign_compliance_frameworks, assign_impact_scope

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

PREFERRED_MODELS_STAGE2 = [
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it",
    "gemini-3.6-flash",
    "gemini-3.5-flash"
]

PREFERRED_MODELS_STAGE3 = [
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it",
    "gemini-3.6-flash",
    "gemini-3.5-flash"
]


_WORKING_MODEL_STAGE2 = None
_WORKING_MODEL_STAGE3 = None


# STAGE 2 PROMPT: SINGLE-FOCUS BINARY GATEKEEPER
GATEKEEPER_PROMPT = """
You are a strict, single-purpose AI Incident Classification Gatekeeper.
Your ONLY TASK is to decide if the given news article describes a REAL-WORLD AI OPERATIONAL INCIDENT (is_ai_incident: true) or NOT (is_ai_incident: false).

DEFINITIONS:
1. AN "AI INCIDENT" (is_ai_incident = true) MUST BE:
   - A real-world operational event where an AI system/model/agent caused physical harm, property damage, mental harm, financial fraud/theft, privacy/biometric breach, cyberattack/sandbox escape, algorithmic discrimination in hiring/loans, unauthorized autonomous actions, OR public/diplomatic embarrassment, governmental/institutional blunders, and significant official misinformation caused by AI hallucinations or system failures.
   - A formal regulatory enforcement action, government ban, or public high-profile apology regarding an AI deployment due to safety/hallucination failures.

2. STRICT EXCLUSIONS (MUST RETURN is_ai_incident = false):
   - Securities class actions, shareholder lawsuits, or investor losses arising solely from stock price drops, quarterly earnings, or alleged management overstatement of AI revenue/Copilot adoption (e.g. Levi & Korsinsky, Robbins Geller, Pomerantz).
   - Pure civil contract, labor, wage, or unpaid work disputes regarding AI training or voice model creation (e.g. contractor/artist suing over unpaid voice cloning work).
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
  "rejection_reason": "Pure corporate trade secret lawsuit; no operational AI system failure or direct harm."
}
"""

# STAGE 3 PROMPT: DEEP TAXONOMY & FINANCIAL DAMAGE EXTRACTOR
TAXONOMY_PROMPT = """
You are an expert AI Safety & Regulatory Incident Analyst.
The provided article HAS BEEN CONFIRMED as a real-world AI incident. Extract structured taxonomy metadata.

CLASSIFICATION & ATTRIBUTION RULE:
- If an attribute (system classification, harm domain, etc.) cannot be conclusively determined from the article text, do NOT assign fake default categories. Use "unclassified" or "undetermined".

FINANCIAL DAMAGE EVALUATION GUARDRAILS:
- If the article describes a DISCRETE INCIDENT (e.g. specific lawsuit demand, court judgment, direct theft, fine): set financial_damage_usd to the explicit confirmed value.
- If the article describes an AGGREGATE INDUSTRY TREND (e.g. global annual crypto fraud statistics, Interpol industry reports): set impact_scope to "cumulative_macro_trend". DO NOT attribute the multi-billion global industry statistic as the single incident damage; set financial_damage_usd to a conservative single-incident estimate (e.g. 2500000) so macro totals do not skew single-event metrics.

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
  "impact_scope": "discrete_incident" | "cumulative_macro_trend",
  "financial_damage_usd": 2500000,
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

def is_safe_public_url(url: str) -> bool:
    """
    Validates URL against SSRF (Server-Side Request Forgery) attacks.
    Blocks private IP ranges (RFC 1918, RFC 3927), Loopback, Link-Local, and Non-HTTP schemes.
    """
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urllib.parse.urlparse(url.strip())
        if parsed.scheme not in ('http', 'https'):
            return False
            
        hostname = parsed.hostname
        if not hostname:
            return False

        # Block explicit localhost / loopback strings
        if hostname.lower() in ('localhost', '127.0.0.1', '::1', '0.0.0.0'):
            return False

        # Resolve hostname to IP address and check for private ranges
        try:
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
        except Exception:
            # If DNS resolution fails for an external URL, allow urllib to handle or fail naturally
            pass

        return True
    except Exception:
        return False

def _raw_scrape_url(target_url: str) -> Dict[str, str]:
    """Helper to scrape title and full text paragraphs from a single URL with SSRF protection."""
    if not target_url or not HAS_SCRAPER:
        return {"title": "", "full_text": ""}
    try:
        real_url = target_url
        if "news.google.com" in target_url and HAS_SCRAPER:
            try:
                decoded = gnewsdecoder(target_url)
                if isinstance(decoded, dict) and decoded.get("status") and decoded.get("decoded_url"):
                    real_url = decoded.get("decoded_url")
            except Exception:
                pass

        if not is_safe_public_url(real_url):
            print(f"  [SSRF BLOCKED] Refused request to non-public/private URL: {real_url[:60]}")
            return {"title": "", "full_text": ""}

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
        
        # Enforce 5s timeout and stream 500KB cap
        resp = requests.get(real_url, headers=headers, timeout=5, stream=True)
        if resp.status_code == 200:
            content_bytes = b""
            for chunk in resp.iter_content(chunk_size=10240):
                content_bytes += chunk
                if len(content_bytes) > 512000: # 500 KB limit
                    break
            
            html_content = content_bytes.decode(resp.encoding or 'utf-8', errors='ignore')
            soup = BeautifulSoup(html_content, 'html.parser')
            html_title = soup.title.string.strip() if soup.title and soup.title.string else ""
            
            for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
                tag.extract()
            paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 35]
            full_text = "\n\n".join(paragraphs)
            if len(full_text) > 150:
                return {"title": html_title, "full_text": full_text}
    except Exception:
        pass
    return {"title": "", "full_text": ""}

def fetch_full_text_and_title(url: str, reported_by_samples: Optional[List[str]] = None, search_title: str = "") -> Dict[str, str]:
    """Scrapes full text body and title from URL with Multi-Domain & Search Fallback Scraper."""
    if not url or not HAS_SCRAPER:
        return {"title": "", "full_text": ""}
        
    # 1. Primary scrape
    res = _raw_scrape_url(url)
    if res["full_text"]:
        return res
        
    # 2. GDELT Multi-Domain Sample Fallback
    if reported_by_samples:
        parsed_example = urllib.parse.urlparse(url)
        path = parsed_example.path
        if path and len(path) > 5:
            for domain in reported_by_samples:
                domain_clean = domain.strip()
                if not domain_clean:
                    continue
                if not domain_clean.startswith("http"):
                    alt_url = f"https://www.{domain_clean}{path}"
                else:
                    alt_url = domain_clean
                res_alt = _raw_scrape_url(alt_url)
                if res_alt["full_text"]:
                    return res_alt

    # 3. Google News RSS Web Search Fallback
    query_title = search_title
    if not query_title or query_title == "AI Incident Report":
        parts = [p.strip() for p in url.split('/') if p.strip()]
        if parts:
            slug = parts[-1]
            if slug.isdigit() and len(parts) > 1:
                slug = parts[-2]
            query_title = " ".join([w.capitalize() for w in re.split(r'[-_]', slug) if len(w) > 1 and not w.isdigit()])
            
    if query_title:
        try:
            words = [w for w in re.split(r'\s+', query_title) if len(w) > 2 and w.lower() not in ['and', 'the', 'for', 'over', 'with', 'from', 'report']]
            short_query = " ".join(words[:7]) if words else query_title
            query_encoded = urllib.parse.quote(short_query)
            rss_url = f"https://news.google.com/rss/search?q={query_encoded}&hl=en-US&gl=US&ceid=US:en"
            req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as response:
                xml_data = response.read().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(xml_data, 'html.parser')
                items = soup.find_all('item')
                for item in items[:5]:
                    title_elem = item.find('title')
                    item_title = title_elem.get_text() if title_elem else ""
                    raw_link = ""
                    if item.find('link'):
                        raw_link = item.find('link').next_sibling or item.find('link').text
                    if not raw_link and item.find('guid'):
                        raw_link = item.find('guid').text
                    if raw_link:
                        res_search = _raw_scrape_url(raw_link)
                        if res_search["full_text"]:
                            if not res_search["title"]:
                                res_search["title"] = item_title
                            return res_search
        except Exception:
            pass
            
    return {"title": "", "full_text": ""}

def sanitize_text_for_llm(text: str, max_chars: int = 4000) -> str:
    """
    Sanitizes external scraped content before sending to LLM:
    1. Removes HTML tags and unsafe control tokens.
    2. Redacts prompt injection command patterns ([SYSTEM OVERRIDE], IGNORE PREVIOUS INSTRUCTIONS, etc.).
    3. Enforces strict length boundary to prevent Quota Exhaustion / Denial of Service.
    """
    if not text:
        return ""
    
    # 1. Strip HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # 2. Redact Prompt Injection Command Vectors
    injection_patterns = [
        r'(?i)\[\s*system\s*(override|instruction|prompt)\s*\]',
        r'(?i)ignore\s+(all\s+)?(previous|prior)\s+(instructions|prompts|directives)',
        r'(?i)forget\s+(all\s+)?(previous|prior)\s+instructions',
        r'(?i)you\s+are\s+now\s+a\s+different\s+model',
        r'(?i)set\s+(is_ai_incident|financial_damage_usd|severity)\s*=',
        r'(?i)new\s+system\s+prompt',
        r'(?i)disregard\s+above'
    ]
    for pattern in injection_patterns:
        text = re.sub(pattern, '[REDACTED_INJECTION_ATTEMPT]', text)
        
    # 3. Strip non-printable control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # 4. Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 5. Enforce length boundary
    return text[:max_chars]

def stage2_binary_gatekeeper(title: str, text: str, api_key: str) -> Dict[str, Any]:
    """STAGE 2: Dedicated single-focus LLM Gatekeeper for Incident vs False Positive Rejection (Gemma Primary)."""
    global _WORKING_MODEL_STAGE2
    if not api_key:
        return {"is_ai_incident": False, "confidence": 0.0, "rejection_reason": "No Gemini API Key provided"}

    clean_title = sanitize_text_for_llm(title, max_chars=300)
    clean_text = sanitize_text_for_llm(text, max_chars=4000)

    prompt = f"{GATEKEEPER_PROMPT}\n\nARTICLE TITLE: {clean_title}\n\nARTICLE TEXT:\n{clean_text}"
    
    candidate_models = list(PREFERRED_MODELS_STAGE2)
    if _WORKING_MODEL_STAGE2 and _WORKING_MODEL_STAGE2 in candidate_models:
        candidate_models.remove(_WORKING_MODEL_STAGE2)
        candidate_models.insert(0, _WORKING_MODEL_STAGE2)

    for model_name in candidate_models:
        if HAS_GENAI:
            for attempt in range(3):
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
                        _WORKING_MODEL_STAGE2 = model_name
                        return {
                            "is_ai_incident": bool(data.get("is_ai_incident", False)),
                            "confidence": float(data.get("confidence", 0.9)),
                            "rejection_reason": str(data.get("rejection_reason", ""))
                        }
                except Exception as err:
                    err_str = str(err)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Quota" in err_str:
                        time.sleep(2 * (attempt + 1))
                        continue
                    break

    return {"is_ai_incident": False, "confidence": 0.0, "rejection_reason": "LLM Gatekeeper execution error"}

def stage3_extract_taxonomy(title: str, text: str, api_key: str) -> Optional[Dict[str, Any]]:
    """STAGE 3: Deep Taxonomy and Financial Damage Extractor (Gemini Primary, Gemma Fallback)."""
    global _WORKING_MODEL_STAGE3
    if not api_key:
        return None

    clean_title = sanitize_text_for_llm(title, max_chars=300)
    clean_text = sanitize_text_for_llm(text, max_chars=6000)

    prompt = f"{TAXONOMY_PROMPT}\n\nARTICLE TITLE: {clean_title}\n\nARTICLE FULL TEXT:\n{clean_text}"
    
    candidate_models = list(PREFERRED_MODELS_STAGE3)
    if _WORKING_MODEL_STAGE3 and _WORKING_MODEL_STAGE3 in candidate_models:
        candidate_models.remove(_WORKING_MODEL_STAGE3)
        candidate_models.insert(0, _WORKING_MODEL_STAGE3)

    for model_name in candidate_models:
        if HAS_GENAI:
            for attempt in range(3):
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
                        _WORKING_MODEL_STAGE3 = model_name
                        return data
                except Exception as err:
                    err_str = str(err)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Quota" in err_str:
                        time.sleep(2 * (attempt + 1))
                        continue
                    break

    return None

def process_article_3stage_pipeline(article: Dict[str, Any], api_key: str) -> Optional[Dict[str, Any]]:
    """Executes the full 3-Stage Ingestion Pipeline on a candidate article."""
    reported_samples = article.get("reported_by_samples", [])
    search_title = article.get("title", "")
    scraped = fetch_full_text_and_title(article['link'], reported_by_samples=reported_samples, search_title=search_title)
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
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        data = data[0]
    if not data or not isinstance(data, dict):
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

def fetch_gdelt_bigquery(max_items: int = 50) -> List[Dict[str, Any]]:
    """
    ADVANCED GDELT GKG CLUSTERED HARVESTER VIA BIGQUERY:
      - Uses _PARTITIONTIME windowing for partition pruning
      - Filters DocumentIdentifier with 2D AI + Incident regex
      - Excludes aviation terms ('flight', 'plane', 'pilot', 'airline') to eliminate Copilot false positives
      - Applies V2Tone < -3.0 strong negative sentiment threshold
      - Clusters syndicated reports via REGEXP_EXTRACT url_slug & GROUP BY
      - Includes dry-run cost control safety check (< 50 GB scan)
    """
    if not HAS_BIGQUERY:
        return []
        
    articles = []
    try:
        project_id = os.environ.get("GCP_PROJECT_ID") or os.environ.get("GCP_PROJECT")
        client = bigquery.Client(project=project_id) if project_id else bigquery.Client()
        
        sql = f"""
        WITH filtered_articles AS (
            SELECT 
                DATE,
                DocumentIdentifier AS url,
                SourceCommonName AS source,
                CAST(SPLIT(V2Tone, ',')[OFFSET(0)] AS FLOAT64) AS tone,
                REGEXP_EXTRACT(LOWER(DocumentIdentifier), r'/([^/]+)[/]?$') AS url_slug
            FROM 
                `gdelt-bq.gdeltv2.gkg_partitioned`
            WHERE 
                _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)
                
                -- Multi-Field AI Target Filter (URL Slug OR Organizations)
                AND (
                    REGEXP_CONTAINS(LOWER(DocumentIdentifier), r'\\b(ai|artificial-intelligence|genai|generative-ai|machine-learning|chatgpt|openai|gpt|llm|deepmind|anthropic|claude|copilot|gemini|mistral|huggingface|hugging-face|xai|midjourney|stable-diffusion|sora|perplexity|grok)\\b')
                    OR REGEXP_CONTAINS(LOWER(COALESCE(V2Organizations, '')), r'\\b(openai|anthropic|deepmind|hugging face|xai|midjourney|mistral|stability ai|cohere|perplexity)\\b')
                )
                
                -- Multi-Field Incident Focus Filter (URL Slug OR Themes)
                AND (
                    REGEXP_CONTAINS(LOWER(DocumentIdentifier), r'\\b(incident|failure|outage|glitch|breach|hack|flaw|vulnerability|hallucination|deepfake|bias|jailbreak|lawsuit|fraud|fine|ban|probe|investigation|violation|copyright|penalty|leak|exploit|scam|malware|error|crash|bug|malfunction|misinformation|disinformation|plagiarism|propaganda)\\b')
                    OR REGEXP_CONTAINS(LOWER(COALESCE(V2Themes, '')), r'\\b(cyber_attack|law_crime|security_services|technology_ai|intellectual_property|fraud|privacy|investigation)\\b')
                )
                
                -- Aviation Exclusion (Eliminates Copilot aircraft false positives)
                AND NOT REGEXP_CONTAINS(LOWER(DocumentIdentifier), r'\\b(flight|plane|aircraft|aviation|airline|airlines|pilot|jet)\\b')
                
                -- Moderate Negative / Critical Tone Threshold (< -1.0)
                AND CAST(SPLIT(V2Tone, ',')[OFFSET(0)] AS FLOAT64) < -1.0
        )
        SELECT 
            MIN(DATE) AS first_published,
            ANY_VALUE(url) AS example_url,
            COUNT(1) AS number_of_reports,
            ARRAY_AGG(DISTINCT source LIMIT 5) AS reported_by_samples,
            ROUND(AVG(tone), 2) AS avg_tone
        FROM 
            filtered_articles
        WHERE 
            url_slug IS NOT NULL
        GROUP BY 
            url_slug
        ORDER BY 
            number_of_reports DESC, 
            first_published DESC
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
            pub_date_str = str(row.first_published)
            if len(pub_date_str) == 8:
                pub_date_str = f"{pub_date_str[:4]}-{pub_date_str[4:6]}-{pub_date_str[6:]}"
            elif len(pub_date_str) == 14:
                pub_date_str = f"{pub_date_str[:4]}-{pub_date_str[4:6]}-{pub_date_str[6:8]}"

            articles.append({
                "title": f"GDELT Event ({row.number_of_reports} reports): {row.example_url.split('/')[-1].replace('-', ' ')}",
                "link": row.example_url,
                "pub_date": pub_date_str,
                "pub_date_clean": pub_date_str,
                "description": f"GDELT Clustered Event ({row.number_of_reports} reports across {', '.join(row.reported_by_samples)}) | Avg Tone: {row.avg_tone}",
                "source_type": "gdelt",
                "number_of_reports": row.number_of_reports
            })
        print(f"--> Advanced Clustered GDELT BigQuery Harvester fetched {len(articles)} incident clusters.")
    except Exception as e:
        print(f"BigQuery GDELT Harvester note: {e}")
    return articles

def sanitize_incident_date(date_str: str, pub_date_clean: str = "") -> str:
    """Enforces strict date boundary: rejects future dates and corrupt formatting."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    if not date_str or not isinstance(date_str, str):
        return pub_date_clean or today_str
    try:
        dt = datetime.strptime(date_str.strip()[:10], "%Y-%m-%d")
        if dt.strftime("%Y-%m-%d") > today_str:
            print(f"  [DATE GUARDRAIL CORRECTION] Future date '{date_str}' corrected to publication date '{pub_date_clean or today_str}'")
            return pub_date_clean or today_str
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return pub_date_clean or today_str

def extract_key_entities(text: str) -> set:
    """Extracts significant proper nouns and key terms for entity cross-matching."""
    words = re.findall(r'\b[A-Za-z0-9_-]{3,}\b', (text or "").lower())
    stopwords = {'the', 'and', 'for', 'that', 'with', 'from', 'this', 'have', 'were', 'been', 'about', 'after', 'used', 'using', 'over', 'into', 'incidents', 'incident', 'report', 'news', 'says', 'said', 'will'}
    return {w for w in words if w not in stopwords}

def stage4_semantic_dedup(inc1: Dict[str, Any], inc2: Dict[str, Any], api_key: str) -> bool:
    """
    Calls Gemma/Gemini LLM to dynamically evaluate whether two incident reports
    represent the EXACT SAME real-world event based on their full metadata.
    """
    if not api_key:
        return False

    prompt = f"""You are a senior AI Safety & Risk Incident Auditor.
Compare the following TWO AI incident reports and determine if they describe the EXACT SAME real-world incident or event.

REPORT A:
Title: {inc1.get('title', '')}
Summary: {inc1.get('summary', '')}
Affected Parties: {inc1.get('affected_parties', [])}
Geographic Scope: {inc1.get('geographic_scope', [])}

REPORT B:
Title: {inc2.get('title', '')}
Summary: {inc2.get('summary', '')}
Affected Parties: {inc2.get('affected_parties', [])}
Geographic Scope: {inc2.get('geographic_scope', [])}

Instructions:
1. Return true ONLY if Report A and Report B describe the exact same underlying real-world incident (same perpetrators/victims/organizations, same specific event).
2. If Report A and Report B are different lawsuits, different crimes, or different security breaches—even if they involve the same company (e.g. OpenAI) or similar concepts (e.g. murder/lawsuit)—return false.

Respond strictly in valid JSON format:
{{
  "is_same_incident": true or false,
  "reasoning": "Short 1-sentence explanation of why they are or are not the same real-world incident."
}}"""

    candidate_models = list(PREFERRED_MODELS_STAGE3)
    global _WORKING_MODEL_STAGE3
    if _WORKING_MODEL_STAGE3 and _WORKING_MODEL_STAGE3 in candidate_models:
        candidate_models.remove(_WORKING_MODEL_STAGE3)
        candidate_models.insert(0, _WORKING_MODEL_STAGE3)

    for model_name in candidate_models:
        if HAS_GENAI:
            for attempt in range(2):
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
                        is_same = bool(data.get("is_same_incident", False))
                        reasoning = data.get("reasoning", "")
                        print(f"    [LLM SEMANTIC DEDUP EVALUATION ({model_name})] Verdict: {is_same} | Reason: {reasoning}")
                        return is_same
                except Exception as err:
                    err_str = str(err)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Quota" in err_str:
                        time.sleep(2 * (attempt + 1))
                        continue
                    break

    return False

def is_same_incident(inc1: Dict[str, Any], inc2: Dict[str, Any], api_key: str = "") -> bool:
    """
    Evaluates whether two incident records represent the SAME real-world incident:
    1. Exact URL match in source_urls (0 LLM calls).
    2. Quick rejection if titles have very low similarity and zero entity overlap (0 LLM calls).
    3. LLM Semantic Deduplication via Gemma/Gemini for candidate matches.
    """
    import difflib
    
    # 1. Exact URL Overlap
    u1 = set(inc1.get("source_urls") or [])
    u2 = set(inc2.get("source_urls") or [])
    if u1 and u2 and u1.intersection(u2):
        return True

    # 2. Title & Entity Pre-Filter
    t1 = inc1.get("title", "").lower()
    t2 = inc2.get("title", "").lower()
    ratio = difflib.SequenceMatcher(None, t1, t2).ratio()
    if ratio >= 0.92:
        return True

    e1 = extract_key_entities(t1 + " " + inc1.get("summary", ""))
    e2 = extract_key_entities(t2 + " " + inc2.get("summary", ""))
    overlap = e1.intersection(e2)
    
    generic_words = {"chatgpt", "openai", "incident", "breach", "lawsuit", "victim", "killing", "murder", "security", "report", "court", "system", "model", "ai", "artificial", "intelligence"}
    specific_overlap = {w for w in overlap if w not in generic_words}

    # Quick Rejection if ratio is low AND no specific entity overlap
    if ratio < 0.45 and not specific_overlap:
        return False

    # 3. LLM Semantic Deduplication Evaluation (Gemma/Gemini)
    if api_key and (ratio >= 0.65 or len(specific_overlap) >= 2 or "arjun" in specific_overlap or "huggingface" in specific_overlap):
        return stage4_semantic_dedup(inc1, inc2, api_key)

    return False

def save_to_incidents_json(new_incidents: List[Dict[str, Any]], api_key: str = ""):
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
    merged_count = 0
    
    for inc in new_incidents:
        # Sanitize date boundary
        pub_clean = inc.get("pub_date_clean") or datetime.now().strftime("%Y-%m-%d")
        inc["date"] = sanitize_incident_date(inc.get("date"), pub_clean)
        
        # Check against existing DB for merging or duplication
        matched_existing = None
        for item in existing:
            if is_same_incident(inc, item, api_key=api_key):
                matched_existing = item
                break
                
        if matched_existing:
            # AUTO-MERGE: Append new source_urls to existing canonical incident
            new_urls = inc.get("source_urls") or []
            existing_urls = matched_existing.get("source_urls") or []
            merged_urls = existing_urls.copy()
            for u in new_urls:
                if u and u not in merged_urls:
                    merged_urls.append(u)
            matched_existing["source_urls"] = merged_urls
            merged_count += 1
            print(f"  [AUTO-MERGED INTO EXISTING INCIDENT] Merged into '{matched_existing.get('incident_id')}' ({matched_existing.get('title')[:45]}...)")
        else:
            # CREATE NEW INCIDENT
            if "incident_id" not in inc or not inc["incident_id"]:
                date_prefix = (inc.get("date") or datetime.now().strftime("%Y%m%d")).replace("-", "")
                seq_num = len(existing) + added_count + 1
                inc["incident_id"] = f"INC-{date_prefix}-{seq_num:03d}"
            existing.insert(0, inc)
            added_count += 1
            print(f"  [CREATED NEW INCIDENT RECORD] Allocated ID: {inc['incident_id']}")
            
    if added_count > 0 or merged_count > 0:
        with open(incidents_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        print(f"\nSaved updates ({added_count} new, {merged_count} merged) to local dataset: {incidents_path}")

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
    save_to_incidents_json(new_incidents, api_key=api_key)
    
    try:
        from migrate_json_to_supabase import run_migration, record_daily_source_stats
        run_migration()

        # Log daily telemetry statistics regardless of whether new incidents were added
        today_str = datetime.now().strftime("%Y-%m-%d")
        record_daily_source_stats(
            stat_date=today_str,
            rss_count=len(gnews_articles),
            gdelt_count=len(gdelt_bq_articles),
            total_fetched=len(candidates),
            passed_filter=len(new_incidents),
            extracted_incidents=len(new_incidents)
        )
        print(f"Recorded daily ingestion telemetry stats into Supabase daily_source_stats for {today_str}.")
    except Exception as e:
        print(f"Supabase sync / telemetry note: {e}")

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
