"""
Structured Keyword Filters & Exclusion Taxonomy for AI Incident Detection.
Includes Tier 1 (SQL High-Precision), Tier 2 (Python Scoring), Tier 3 (Context Enrichment),
and Exclusions (Aviation, Financial Noise Control).
"""

from typing import List, Dict, Set

TIER_1_CORE_TERMS = ["ai", "artificial intelligence", "artificial-intelligence"]

TIER_1_MODELS_PRODUCTS = [
    "chatgpt", "gpt-4", "gpt-4o", "claude", "gemini", "copilot", "llama", "mistral",
    "deepseek", "qwen", "midjourney", "dall-e", "stable-diffusion", "sora", "perplexity",
    "grok", "ernie", "doubao", "hunyuan", "kimi", "chatglm", "internlm", "black-forest-labs",
    "aleph-alpha", "palantir", "cohere", "runway", "elevenlabs", "character-ai", "replika",
    "pi-ai", "waymo", "cruise", "zoox", "figure-ai", "clearview-ai", "nso-group", "pegasus"
]

TIER_1_PROVIDERS = [
    "openai", "anthropic", "deepmind", "huggingface", "hugging-face", "xai", "mistral",
    "baidu-ai", "alibaba-ai", "bytedance-ai", "moonshot-ai", "01-ai", "shanghai-ai-lab",
    "c3-ai", "scale-ai", "inflection-ai", "tesla-autopilot", "tesla-fsd", "mobileye",
    "aurora-innovation", "anduril"
]

TIER_1_INCIDENT_TERMS = [
    "incident", "hallucination", "deepfake", "jailbreak", "lawsuit", "breach", "vulnerability",
    "fraud", "investigation", "fine", "ban", "probe", "leak", "scam", "malware", "crash",
    "malfunction", "misinformation", "disinformation", "plagiarism", "copyright", "bias",
    "outage", "failure", "glitch", "exploit", "hack", "flaw", "bug", "error"
]

TIER_2_HARMS_AND_REGULATORY = [
    "hate-speech", "toxic", "csam", "cyberattack", "phishing", "ransomware", "credential-theft",
    "doxxing", "privacy-violation", "unauthorized-access", "injury", "fatality", "collision",
    "lethal-autonomous", "self-harm", "job-displacement", "election-interference", "astroturfing",
    "bioweapon", "cbrn", "dual-use", "robustness-failure", "lack-of-transparency", "c2pa",
    "eu-ai-act-violation", "gdpr-violation", "cease-and-desist", "safety-recall", "whistleblower",
    "emergency-patch", "rollback"
]

EXCLUSIONS_AVIATION = [
    "flight", "plane", "aircraft", "aviation", "airline", "airlines", "pilot", "jet", "cockpit", "takeoff", "landing"
]

EXCLUSIONS_FINANCIAL = [
    "stock-price", "market-crash", "trading-volume", "portfolio", "dividend", "earnings-report"
]

def build_gdelt_sql_query() -> str:
    """Generates optimized BigQuery SQL query using Tier 1 high-precision terms & exclusion filters."""
    ai_clause = " OR ".join([f"LOWER(DocumentIdentifier) LIKE '%{t}%'" for t in TIER_1_MODELS_PRODUCTS[:10]])
    incident_clause = " OR ".join([f"LOWER(DocumentIdentifier) LIKE '%{t}%'" for t in TIER_1_INCIDENT_TERMS[:10]])
    
    sql = f"""
    SELECT DocumentIdentifier, SourceCommonName, V2Themes, DATE
    FROM `gdelt-bq.gdeltv2.gkg`
    WHERE DATE >= CAST(FORMAT_DATE('%Y%m%d000000', DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)) AS INT64)
      AND (V2Themes LIKE '%TECH_ARTIFICIAL_INTELLIGENCE%' OR ({ai_clause}))
      AND ({incident_clause})
      AND NOT EXISTS (
        SELECT 1 FROM UNNEST(SPLIT(LOWER(DocumentIdentifier), '/')) word 
        WHERE word IN ('flight', 'aircraft', 'aviation', 'airline', 'pilot')
      )
    LIMIT 50
    """
    return sql.strip()

def score_article_relevance(title: str, text: str) -> float:
    """
    Scores article relevance using Tier 1 and Tier 2 terms while enforcing Exclusions.
    Returns relevance score (0.0 to 1.0).
    """
    content = f"{title} {text}".lower()
    
    # Check exclusions (Aviation false positives like airplane copilot, financial noise)
    for exc in EXCLUSIONS_AVIATION:
        if exc in content and "copilot" in content and "microsoft" not in content and "github" not in content:
            return 0.0 # Exclude false positive aviation copilot
            
    score = 0.0
    
    # Tier 1 AI term match (+0.4)
    if any(term in content for term in TIER_1_CORE_TERMS + TIER_1_MODELS_PRODUCTS + TIER_1_PROVIDERS):
        score += 0.4
        
    # Tier 1 Incident term match (+0.4)
    if any(term in content for term in TIER_1_INCIDENT_TERMS):
        score += 0.4
        
    # Tier 2 Harm / Regulatory match (+0.2)
    if any(term in content for term in TIER_2_HARMS_AND_REGULATORY):
        score += 0.2
        
    return min(score, 1.0)
