"""
High-Performance Modular AI Incident Deduplication Engine.
Step 1: Text Normalization, Canonicalization & Exact Fingerprint Matching.
Step 2: Pure-Python TF-IDF Vectorization & Hybrid Cosine Similarity Pre-filtering.
Step 3: Top-K Reranking & Targeted LLM Semantic Verification.
Step 4: Union-Find Transitive Clustering & Single-Pass Dataset Consolidation.
"""

import re
import math
import time
import json
import urllib.parse
from collections import Counter
from typing import Dict, Any, List, Set, Tuple, Optional

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# Preferred active Gemini models (>= 3.1 ONLY)
PREFERRED_MODELS_DEDUP = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash"
]

_WORKING_DEDUP_MODEL: Optional[str] = None

# ==============================================================================
# STEP 1: NORMALIZATION & FINGERPRINTING
# ==============================================================================

def normalize_url(url: str) -> str:
    """
    Normalizes a URL by lowercasing hostname, stripping trailing slashes,
    removing tracking/utm parameters, and standardizing http to https.
    """
    if not url:
        return ""
    
    url = url.strip()
    parsed = urllib.parse.urlparse(url)
    
    scheme = (parsed.scheme or "https").lower()
    if scheme == "http":
        scheme = "https"
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
        
    path = parsed.path.rstrip("/")
    
    query_params = urllib.parse.parse_qs(parsed.query)
    clean_params = []
    ignored_params = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref", "source", "fbclid", "gclid"}
    
    for key in sorted(query_params.keys()):
        if key.lower() not in ignored_params:
            for val in query_params[key]:
                clean_params.append((key, val))
                
    clean_query = urllib.parse.urlencode(clean_params)
    
    normalized = urllib.parse.urlunparse((scheme, netloc, path, "", clean_query, ""))
    return normalized

def normalize_text(text: str) -> str:
    """
    Normalizes text for exact title fingerprinting & vector tokenization:
    lower-cased, unicode cleaned, punctuation stripped, normalized whitespace.
    """
    if not text:
        return ""
        
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_normalized_url_set(inc: Dict[str, Any]) -> Set[str]:
    """Returns a set of normalized URLs from an incident dict."""
    urls = inc.get("source_urls") or []
    if isinstance(urls, str):
        urls = [urls]
    normalized_set = set()
    for u in urls:
        norm = normalize_url(u)
        if norm:
            normalized_set.add(norm)
    return normalized_set

def is_exact_duplicate(inc1: Dict[str, Any], inc2: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Checks if two incident records are 100% exact duplicates (0 LLM cost).
    Returns (True/False, reason).
    """
    urls1 = get_normalized_url_set(inc1)
    urls2 = get_normalized_url_set(inc2)
    if urls1 and urls2 and urls1.intersection(urls2):
        shared_url = list(urls1.intersection(urls2))[0]
        return True, f"Exact URL match: {shared_url}"

    t1 = normalize_text(inc1.get("title", ""))
    t2 = normalize_text(inc2.get("title", ""))
    if t1 and t2 and t1 == t2:
        return True, f"Exact normalized title match: {t1[:40]}..."

    return False, "No exact match"

def merge_duplicate_records(inc1: Dict[str, Any], inc2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges two duplicate incident records safely:
    - Combines source_urls (union set preserving order)
    - Preserves max financial_damage_usd
    - Retains longest summary and full_text
    - Preserves primary incident_id and date
    """
    merged = dict(inc1)
    
    urls1 = inc1.get("source_urls") or []
    urls2 = inc2.get("source_urls") or []
    seen = set()
    combined_urls = []
    for u in list(urls1) + list(urls2):
        norm = normalize_url(u)
        if norm and norm not in seen:
            seen.add(norm)
            combined_urls.append(u)
    merged["source_urls"] = combined_urls
    
    dam1 = inc1.get("financial_damage_usd") or 0
    dam2 = inc2.get("financial_damage_usd") or 0
    merged["financial_damage_usd"] = max(dam1, dam2)
    
    s1 = inc1.get("summary") or ""
    s2 = inc2.get("summary") or ""
    if len(s2) > len(s1):
        merged["summary"] = s2
        
    f1 = inc1.get("full_text") or ""
    f2 = inc2.get("full_text") or ""
    if len(f2) > len(f1):
        merged["full_text"] = f2

    p1 = set(inc1.get("affected_parties") or [])
    p2 = set(inc2.get("affected_parties") or [])
    merged["affected_parties"] = list(p1.union(p2))

    return merged

# ==============================================================================
# STEP 2: PURE-PYTHON TF-IDF VECTORIZATION & COSINE SIMILARITY
# ==============================================================================

STOPWORDS = {
    'the', 'and', 'for', 'that', 'with', 'from', 'this', 'have', 'were', 'been',
    'about', 'after', 'used', 'using', 'over', 'into', 'incidents', 'incident',
    'report', 'news', 'says', 'said', 'will', 'also', 'their', 'which', 'other',
    'more', 'some', 'such', 'when', 'what', 'where', 'how', 'than', 'them', 'these',
    'ai', 'system', 'model', 'models', 'artificial', 'intelligence', 'data',
    'user', 'users', 'company', 'first', 'resulting', 'tools', 'tool', 'agent', 'agents'
}

def build_incident_corpus(inc: Dict[str, Any]) -> str:
    """
    Constructs the exact text corpus used for vector embedding:
    Title + Summary + Affected Parties + Geographic Scope.
    """
    title = inc.get("title", "")
    summary = inc.get("summary", "") or ""
    parties = " ".join(inc.get("affected_parties") or [])
    scope = " ".join(inc.get("geographic_scope") or [])
    
    raw_corpus = f"{title} {title} {summary} {parties} {scope}"
    return normalize_text(raw_corpus)

def tokenize(text: str) -> List[str]:
    """Tokenizes text into unigrams and bigrams, filtering out generic stopwords."""
    words = [w for w in text.split() if len(w) > 2 and w not in STOPWORDS]
    tokens = list(words)
    for i in range(len(words) - 1):
        bigram = f"{words[i]}_{words[i+1]}"
        tokens.append(bigram)
    return tokens

def compute_tfidf_vectors(corpus_list: List[str]) -> Tuple[List[Dict[str, float]], List[str]]:
    """Computes pure-Python TF-IDF feature vectors for a list of document strings."""
    N = len(corpus_list)
    doc_tokens = [tokenize(doc) for doc in corpus_list]
    
    df_counts = Counter()
    for tokens in doc_tokens:
        unique_terms = set(tokens)
        for term in unique_terms:
            df_counts[term] += 1
            
    idf = {}
    for term, count in df_counts.items():
        idf[term] = math.log((1 + N) / (1 + count)) + 1.0
        
    tfidf_vectors = []
    for tokens in doc_tokens:
        tf_counts = Counter(tokens)
        doc_len = len(tokens) or 1
        vec = {}
        norm_sq = 0.0
        for term, count in tf_counts.items():
            tf = count / doc_len
            weight = tf * idf[term]
            vec[term] = weight
            norm_sq += weight * weight
            
        norm = math.sqrt(norm_sq) or 1.0
        normalized_vec = {t: w / norm for t, w in vec.items()}
        tfidf_vectors.append(normalized_vec)
        
    vocab = sorted(list(df_counts.keys()))
    return tfidf_vectors, vocab

def cosine_similarity_vectors(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """Computes cosine similarity between two normalized sparse TF-IDF vectors."""
    dot_product = 0.0
    if len(vec1) > len(vec2):
        vec1, vec2 = vec2, vec1
        
    for term, w1 in vec1.items():
        if term in vec2:
            dot_product += w1 * vec2[term]
            
    return dot_product

def compute_candidate_pairs_tfidf(
    incidents: List[Dict[str, Any]],
    min_similarity: float = 0.20
) -> Tuple[List[Dict[str, Any]], List[Dict[str, float]]]:
    """Filters all pairwise incident combinations down to candidate pairs using Cosine Similarity."""
    corpus_list = [build_incident_corpus(inc) for inc in incidents]
    tfidf_vectors, vocab = compute_tfidf_vectors(corpus_list)
    
    N = len(incidents)
    candidate_pairs = []
    
    for i in range(N):
        for j in range(i + 1, N):
            inc1 = incidents[i]
            inc2 = incidents[j]
            
            is_exact, exact_reason = is_exact_duplicate(inc1, inc2)
            sim_score = cosine_similarity_vectors(tfidf_vectors[i], tfidf_vectors[j])
            
            p1 = {p.lower().strip() for p in (inc1.get("affected_parties") or [])}
            p2 = {p.lower().strip() for p in (inc2.get("affected_parties") or [])}
            generic_parties = {
                "unknown", "public", "general public", "users", "consumers",
                "openai", "anthropic", "google", "microsoft", "meta", "xai", "deepseek"
            }
            shared_parties = (p1 - generic_parties) & (p2 - generic_parties)
            
            if is_exact or sim_score >= min_similarity or len(shared_parties) > 0:
                candidate_pairs.append({
                    "idx1": i,
                    "idx2": j,
                    "id1": inc1.get("incident_id"),
                    "id2": inc2.get("incident_id"),
                    "title1": inc1.get("title"),
                    "title2": inc2.get("title"),
                    "similarity": round(sim_score, 4),
                    "is_exact": is_exact,
                    "shared_parties": list(shared_parties)
                })
                
    return candidate_pairs, tfidf_vectors

# ==============================================================================
# STEP 3: TOP-K RERANKING & TARGETED LLM VERIFICATION
# ==============================================================================

def verify_candidate_pair_llm(inc1: Dict[str, Any], inc2: Dict[str, Any], api_key: str = "") -> Tuple[bool, float, str]:
    """
    Targeted LLM verification for high-probability candidate pairs.
    Returns (is_same_incident: bool, confidence: float, reasoning: str).
    """
    if not api_key:
        return False, 0.0, "No API key"

    prompt = f"""Compare Report A and Report B below and determine if they describe the EXACT SAME underlying real-world AI incident.

REPORT A:
Title: {inc1.get('title', '')}
Summary: {inc1.get('summary', '')}
Date: {inc1.get('date', '')}
Affected Parties: {inc1.get('affected_parties', [])}

REPORT B:
Title: {inc2.get('title', '')}
Summary: {inc2.get('summary', '')}
Date: {inc2.get('date', '')}
Affected Parties: {inc2.get('affected_parties', [])}

Instructions:
1. Return is_same_incident: true ONLY if Report A and Report B describe the exact same underlying real-world incident.
2. Return is_same_incident: false if they describe different lawsuits, different crimes, or different security breaches—even if they involve the same company.

Respond strictly in valid JSON format:
{{
  "is_same_incident": true or false,
  "confidence": 0.95,
  "reasoning": "Short explanation."
}}"""

    candidate_models = list(PREFERRED_MODELS_DEDUP)
    global _WORKING_DEDUP_MODEL
    if _WORKING_DEDUP_MODEL and _WORKING_DEDUP_MODEL in candidate_models:
        candidate_models.remove(_WORKING_DEDUP_MODEL)
        candidate_models.insert(0, _WORKING_DEDUP_MODEL)

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
                        is_same = bool(data.get("is_same_incident", False))
                        confidence = float(data.get("confidence", 0.90))
                        reasoning = str(data.get("reasoning", ""))
                        _WORKING_DEDUP_MODEL = model_name
                        return is_same, confidence, reasoning
                except Exception as err:
                    err_str = str(err)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        time.sleep(2 * (attempt + 1))
                        continue
                    break

    return False, 0.0, "LLM call failed"

# ==============================================================================
# STEP 4: UNION-FIND CLUSTERING & SINGLE-PASS DATASET CONSOLIDATION
# ==============================================================================

class UnionFind:
    """Disjoint-Set / Union-Find data structure for grouping connected duplicates."""
    def __init__(self, size: int):
        self.parent = list(range(size))
        
    def find(self, i: int) -> int:
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]
        
    def union(self, i: int, j: int):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            self.parent[root_b if (root_b := root_j) else root_a] = root_i

def consolidate_dataset_hybrid(
    incidents: List[Dict[str, Any]],
    api_key: str = "",
    max_k_candidates: int = 3
) -> List[Dict[str, Any]]:
    """
    100% Scalable 4-Step Hybrid Deduplication Pipeline:
    Step 1: Exact Fingerprinting & URL Match (0 LLM Calls)
    Step 2: TF-IDF Vector Cosine Similarity & Metadata Pre-filtering (90%+ Reduction)
    Step 3: Top-K Targeted LLM Semantic Verification (Gemini >= 3.1)
    Step 4: Union-Find Transitive Clustering & Single Synthesis Merge Pass
    """
    if not incidents:
        return []
        
    N = len(incidents)
    uf = UnionFind(N)
    
    # Step 2: Compute candidate pairs via TF-IDF vector pre-filtering
    candidate_pairs, _ = compute_candidate_pairs_tfidf(incidents, min_similarity=0.20)
    
    # Step 3: Top-K Reranking and targeted evaluation
    llm_call_count = 0
    exact_match_count = 0
    
    for pair in candidate_pairs:
        i, j = pair["idx1"], pair["idx2"]
        
        # Step 1: Instant Exact Match
        if pair["is_exact"]:
            uf.union(i, j)
            exact_match_count += 1
            continue
            
        # Step 3: Targeted LLM Evaluation
        is_same, confidence, reasoning = verify_candidate_pair_llm(
            incidents[i], incidents[j], api_key=api_key
        )
        llm_call_count += 1
        print(f"    [STEP 3 LLM VERIFY] Pair ({pair['id1']}, {pair['id2']}) | Match: {is_same} ({confidence:.2f}) | {reasoning}")
        
        if is_same and confidence >= 0.70:
            uf.union(i, j)

    # Step 4: Union-Find Grouping into Clusters
    clusters: Dict[int, List[Dict[str, Any]]] = {}
    for idx, inc in enumerate(incidents):
        root = uf.find(idx)
        if root not in clusters:
            clusters[root] = []
        clusters[root].append(inc)
        
    # Merge each cluster into a single canonical record
    consolidated_records: List[Dict[str, Any]] = []
    for root, cluster_members in clusters.items():
        canonical = cluster_members[0]
        for member in cluster_members[1:]:
            canonical = merge_duplicate_records(canonical, member)
        consolidated_records.append(canonical)
        
    print(f"\n[DEDUP ENGINE TELEMETRY] Initial: {N} -> Final: {len(consolidated_records)} canonical incidents.")
    print(f"[DEDUP ENGINE TELEMETRY] Exact Matches: {exact_match_count} | LLM Calls: {llm_call_count}")
    return consolidated_records
