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
from datetime import datetime
from functools import lru_cache
from collections import Counter
from typing import Dict, Any, List, Set, Tuple, Optional

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# Preferred active models (Gemma-4-26B primary, Gemini >= 3.1 fallback)
PREFERRED_MODELS_DEDUP = [
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite"
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
    if not url or not url.strip():
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

def merge_duplicate_records(
    inc1: Dict[str, Any],
    inc2: Dict[str, Any],
    milestone_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Merges two duplicate incident records safely:
    - Combines source_urls (union set preserving order)
    - Preserves max financial_damage_usd
    - Retains longest summary and full_text
    - Preserves primary incident_id and earliest publication date
    - Maintains chronological Event-Chain timeline of milestones
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

    # Verification status promotion (unverified -> confirmed if any report confirms)
    v1 = inc1.get("verification_status") or "unverified"
    v2 = inc2.get("verification_status") or "unverified"
    if "confirmed" in (v1, v2):
        merged["verification_status"] = "confirmed"

    # First-Reported-Date principle: primary date is always the earliest publication date
    d1 = inc1.get("date") or "9999-99-99"
    d2 = inc2.get("date") or "9999-99-99"
    earliest_date = min(d1, d2)
    if earliest_date != "9999-99-99":
        merged["date"] = earliest_date

    # ==========================================================================
    # EVENT-CHAIN / TIMELINE CONSOLIDATION
    # ==========================================================================
    timeline: List[Dict[str, Any]] = []
    existing_t1 = inc1.get("timeline") or []
    if existing_t1 and isinstance(existing_t1, list):
        timeline.extend(existing_t1)
    elif inc1.get("title"):
        # Initialize anchor milestone for inc1
        first_sentence_1 = (inc1.get("summary") or "").strip().split(". ")[0]
        if first_sentence_1 and not first_sentence_1.endswith("."):
            first_sentence_1 += "."
        timeline.append({
            "date": inc1.get("date") or "",
            "title": inc1.get("title") or "",
            "summary_delta": first_sentence_1 or (inc1.get("title") or ""),
            "phase": "initial_report",
            "source_url": (urls1 or [""])[0],
            "source_type": inc1.get("source_type") or "google_news_rss"
        })

    # Collect milestones from inc2
    incoming_milestones: List[Dict[str, Any]] = []
    existing_t2 = inc2.get("timeline") or []
    if existing_t2 and isinstance(existing_t2, list):
        incoming_milestones.extend(existing_t2)
    elif inc2.get("title"):
        m_phase = "follow_up"
        s_delta = ""
        if milestone_info:
            m_phase = milestone_info.get("milestone_phase") or "follow_up"
            s_delta = milestone_info.get("summary_delta") or ""
        if not s_delta:
            s_delta = (inc2.get("summary") or "").strip().split(". ")[0]
            if s_delta and not s_delta.endswith("."):
                s_delta += "."
        incoming_milestones.append({
            "date": inc2.get("date") or "",
            "title": inc2.get("title") or "",
            "summary_delta": s_delta or (inc2.get("title") or ""),
            "phase": m_phase,
            "source_url": (urls2 or [""])[0],
            "source_type": inc2.get("source_type") or "google_news_rss"
        })

    # Deduplicate milestones by normalized source_url and (date + normalized title)
    seen_timeline_urls = set()
    seen_date_titles = set()
    for m in timeline:
        u_norm = normalize_url(m.get("source_url") or "")
        if u_norm:
            seen_timeline_urls.add(u_norm)
        dt_key = (m.get("date") or "", normalize_text(m.get("title") or ""))
        seen_date_titles.add(dt_key)

    for m in incoming_milestones:
        u_norm = normalize_url(m.get("source_url") or "")
        dt_key = (m.get("date") or "", normalize_text(m.get("title") or ""))
        if u_norm and u_norm in seen_timeline_urls:
            continue
        if dt_key in seen_date_titles:
            continue

        # Skip redundant copy on the exact same date if classified as redundant
        if milestone_info and milestone_info.get("evolution_type") == "redundant_copy" and m.get("date") == merged.get("date"):
            continue

        timeline.append(m)
        if u_norm:
            seen_timeline_urls.add(u_norm)
        seen_date_titles.add(dt_key)

    # Sort timeline chronologically by date
    timeline.sort(key=lambda item: item.get("date") or "9999-99-99")

    # Mark the chronological earliest milestone as initial_report
    if timeline and timeline[0].get("phase") != "initial_report":
        timeline[0]["phase"] = "initial_report"

    # Compute latest activity / last_updated_date
    valid_dates = [m.get("date") for m in timeline if m.get("date")]
    if valid_dates:
        merged["last_updated_date"] = max(valid_dates)

    merged["timeline"] = timeline
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

GENERIC_PARTIES = {
    "unknown", "public", "general public", "users", "consumers",
    "openai", "anthropic", "google", "microsoft", "meta", "xai", "deepseek"
}

MAJOR_AI_VENDORS = {
    "openai", "anthropic", "google", "microsoft", "meta", "xai", "deepseek",
    "character.ai", "character ai", "huggingface", "hugging face", "waymo", "tesla"
}

GENERIC_ENTITY_TOKENS = STOPWORDS | GENERIC_PARTIES | {
    "department", "ministry", "state", "government", "family", "system", "systems",
    "agency", "police", "hospital", "public", "office", "court", "bank", "banks",
    "services", "commission", "university", "company", "companies", "corporation",
    "group", "students", "parents", "community", "organization", "organizations",
    "officials", "authorities", "researchers", "patients", "victims", "citizens",
    "employees", "workers", "customers", "clients", "children", "minors", "teens",
    "schools", "school", "district", "county", "city", "national", "federal",
    "international", "global", "united", "states", "south", "north", "east", "west",
    "central", "general", "health", "medical", "financial", "commercial", "security",
    "safety", "platform", "network", "networks", "software", "technology", "technologies"
}

@lru_cache(maxsize=8192)
def stem_word(word: str) -> str:
    """Deterministic suffix/prefix stemmer for English morphological variants."""
    if len(word) <= 4:
        return word
    for suffix in (
        "ations", "ation", "itions", "ition", "ings", "ing",
        "ments", "ment", "ities", "ity", "nesses", "ness", "ed", "es", "s"
    ):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            base = word[:-len(suffix)]
            return base[:6] if len(base) >= 6 else base
    return word[:6] if len(word) >= 6 else word

def extract_distinct_entity_tokens(parties: Set[str]) -> Set[str]:
    """Extracts non-generic proper-noun / entity tokens (>= 4 chars) from a set of party names."""
    tokens = set()
    for p in parties:
        for w in normalize_text(p).split():
            if len(w) >= 4 and w not in GENERIC_ENTITY_TOKENS and not w.isdigit():
                tokens.add(w)
    return tokens

def extract_incident_entity_metadata(inc: Dict[str, Any]) -> Dict[str, Any]:
    """Pre-computes normalized entity tokens, words, date, and scope sets for fast candidate matching."""
    p = {p.lower().strip() for p in (inc.get("affected_parties") or [])} - GENERIC_PARTIES
    t = extract_distinct_entity_tokens(p)
    long_t = {tok for tok in t if len(tok) >= 5}
    text_words = set(normalize_text(f"{inc.get('title', '')} {inc.get('summary', '')}").split())
    date_str = str(inc.get("date", ""))[:10]
    dt = None
    if date_str:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            dt = None
    all_p = {p.lower().strip() for p in (inc.get("affected_parties") or [])} | set(normalize_text(inc.get("title", "")).split())
    g = {g.lower().strip() for g in (inc.get("geographic_scope") or [])} - {"global", "united states", "unknown"}
    return {
        "parties": p,
        "tokens": t,
        "long_tokens": long_t,
        "words": text_words,
        "dt": dt,
        "all_p": all_p,
        "g": g,
    }

def compute_boost_from_metadata(meta1: Dict[str, Any], meta2: Dict[str, Any]) -> Tuple[float, Set[str]]:
    """Fast boost computation directly operating on pre-computed metadata sets without repeated parsing/regexes."""
    exact_shared = meta1["parties"] & meta2["parties"]
    t1 = meta1["tokens"]
    t2 = meta2["tokens"]
    shared_subtokens = t1 & t2

    text1_words = meta1["words"]
    text2_words = meta2["words"]
    cross_shared = (
        (meta1["long_tokens"] & text2_words)
        | (meta2["long_tokens"] & text1_words)
    )

    all_shared_entities = exact_shared | shared_subtokens | cross_shared
    if exact_shared or len(shared_subtokens) >= 1 or len(cross_shared) >= 2:
        entity_boost = 0.20
    elif len(cross_shared) == 1:
        entity_boost = 0.12
    else:
        entity_boost = 0.0

    temporal_boost = 0.0
    d1 = meta1["dt"]
    d2 = meta2["dt"]
    if d1 is not None and d2 is not None:
        days_apart = abs((d1 - d2).days)
    else:
        days_apart = 999

    if days_apart <= 7:
        shared_vendors = (meta1["all_p"] & meta2["all_p"]) & MAJOR_AI_VENDORS
        if shared_vendors or (meta1["g"] & meta2["g"]):
            temporal_boost = 0.08

    return entity_boost + temporal_boost, all_shared_entities

def compute_entity_and_temporal_boost(inc1: Dict[str, Any], inc2: Dict[str, Any]) -> Tuple[float, Set[str]]:
    """
    Computes hybrid candidate boost combining:
    1. Exact & Sub-Token Entity Overlap across affected_parties and title/summary.
    2. Temporal + Vendor / Geographic Scope proximity boost (<= 7 days).
    Returns (total_boost, shared_entity_identifiers).
    """
    return compute_boost_from_metadata(
        extract_incident_entity_metadata(inc1),
        extract_incident_entity_metadata(inc2)
    )

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
    """Tokenizes text into unigrams, morphological stems, and bigrams, filtering out generic stopwords."""
    words = [w for w in text.split() if len(w) > 2 and w not in STOPWORDS]
    tokens = list(words)
    for w in words:
        if len(w) >= 5:
            tokens.append(f"st_{stem_word(w)}")
    for i in range(len(words) - 1):
        bigram = f"{words[i]}_{words[i+1]}"
        tokens.append(bigram)
    return tokens

def build_tfidf_index(corpus_list: List[str]) -> Tuple[List[Dict[str, float]], Dict[str, float], int]:
    """
    Computes smoothed IDF dictionary and L2-normalized sparse vectors for a corpus of documents.
    Returns (tfidf_vectors, idf_dictionary, total_documents).
    """
    N = len(corpus_list)
    if N == 0:
        return [], {}, 0

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

    return tfidf_vectors, idf, N


def vectorize_single_document(
    doc: str,
    idf_dict: Dict[str, float],
    total_docs: int
) -> Dict[str, float]:
    """
    Incrementally projects a single document against a pre-computed IDF dictionary in O(L) time.
    Applies L2 normalization.
    """
    tokens = tokenize(doc)
    tf_counts = Counter(tokens)
    doc_len = len(tokens) or 1

    # Smooth IDF default for terms not in canonical catalog
    default_idf = math.log(1 + max(total_docs, 1)) + 1.0

    vec = {}
    norm_sq = 0.0
    for term, count in tf_counts.items():
        tf = count / doc_len
        weight = tf * idf_dict.get(term, default_idf)
        vec[term] = weight
        norm_sq += weight * weight

    norm = math.sqrt(norm_sq) or 1.0
    return {t: w / norm for t, w in vec.items()}


class TermIndex(dict):
    """
    Hybrid term index preserving 100% backward compatibility:
    Behaves as Dict[str, float] (term -> idf) while supporting sequence/list-like indexing and iteration.
    """
    def __init__(self, idf_dict: Dict[str, float]):
        super().__init__(idf_dict)
        self._term_list = sorted(list(idf_dict.keys()))

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, int):
            return self._term_list[key]
        return super().__getitem__(key)

    def __iter__(self):
        return iter(self._term_list)


def compute_tfidf_vectors(corpus_list: List[str]) -> Tuple[List[Dict[str, float]], Any]:
    """
    Computes pure-Python TF-IDF feature vectors for a list of document strings.
    Maintains 100% backward compatibility returning (vectors, TermIndex(idf_dict)).
    """
    tfidf_vectors, idf, _ = build_tfidf_index(corpus_list)
    return tfidf_vectors, TermIndex(idf)


def cosine_similarity_vectors(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """Computes cosine similarity between two normalized sparse TF-IDF vectors."""
    dot_product = 0.0
    if len(vec1) > len(vec2):
        vec1, vec2 = vec2, vec1
        
    for term, w1 in vec1.items():
        w2 = vec2.get(term)
        if w2 is not None:
            dot_product += w1 * w2
            
    return dot_product

def compute_candidate_pairs_tfidf(
    incidents: List[Dict[str, Any]],
    min_similarity: float = 0.18
) -> Tuple[List[Dict[str, Any]], List[Dict[str, float]]]:
    """Filters all pairwise incident combinations down to candidate pairs using Cosine Similarity & Entity/Temporal Boost."""
    corpus_list = [build_incident_corpus(inc) for inc in incidents]
    tfidf_vectors, vocab = compute_tfidf_vectors(corpus_list)
    metadata_list = [extract_incident_entity_metadata(inc) for inc in incidents]
    
    N = len(incidents)
    candidate_pairs = []
    
    for i in range(N):
        for j in range(i + 1, N):
            inc1 = incidents[i]
            inc2 = incidents[j]
            
            is_exact, exact_reason = is_exact_duplicate(inc1, inc2)
            sim_score = cosine_similarity_vectors(tfidf_vectors[i], tfidf_vectors[j])
            boost, shared_parties = compute_boost_from_metadata(metadata_list[i], metadata_list[j])
            effective_score = sim_score + boost
            
            if is_exact or effective_score >= min_similarity or len(shared_parties) > 0:
                candidate_pairs.append({
                    "idx1": i,
                    "idx2": j,
                    "id1": inc1.get("incident_id"),
                    "id2": inc2.get("incident_id"),
                    "title1": inc1.get("title"),
                    "title2": inc2.get("title"),
                    "similarity": round(sim_score, 4),
                    "effective_score": round(effective_score, 4),
                    "is_exact": is_exact,
                    "shared_parties": list(shared_parties)
                })
                
    return candidate_pairs, tfidf_vectors

# ==============================================================================
# STEP 3: TOP-K RERANKING & TARGETED LLM VERIFICATION
# ==============================================================================

def verify_candidate_pair_llm(
    inc1: Dict[str, Any],
    inc2: Dict[str, Any],
    api_key: str = ""
) -> Tuple[bool, float, str, Dict[str, Any]]:
    """
    Targeted LLM verification for high-probability candidate pairs.
    Returns (is_same_incident: bool, confidence: float, reasoning: str, milestone_info: Dict[str, Any]).
    """
    default_milestone = {"evolution_type": "redundant_copy", "milestone_phase": "follow_up", "summary_delta": ""}
    if not api_key:
        return False, 0.0, "No API key", default_milestone

    alleged_date_1 = inc1.get('alleged_incident_date') or 'Not specified (use publication date)'
    alleged_date_2 = inc2.get('alleged_incident_date') or 'Not specified (use publication date)'

    prompt = f"""Compare Report A and Report B below and determine if they describe the EXACT SAME underlying real-world AI incident or event.

REPORT A:
Title: {inc1.get('title', '')}
Summary: {inc1.get('summary', '')}
Article Publication Date: {inc1.get('date', '')}
Alleged Incident Event Date: {alleged_date_1}
Affected Parties: {inc1.get('affected_parties', [])}

REPORT B:
Title: {inc2.get('title', '')}
Summary: {inc2.get('summary', '')}
Article Publication Date: {inc2.get('date', '')}
Alleged Incident Event Date: {alleged_date_2}
Affected Parties: {inc2.get('affected_parties', [])}

Instructions:
1. Return is_same_incident: true ONLY if Report A and Report B describe the exact same underlying real-world incident.
2. Reporting Date vs Event Date: "Article Publication Date" merely reflects when news outlets published an article. A follow-up investigation, court settlement, government audit, or retrospective report published weeks or months later about the same real-world incident is STILL the same incident. Do NOT treat different publication dates as different incidents if the underlying core event, victim, or technology failure is the same.
3. Evolving Media Attribution: News reporting evolves over time. Earlier articles may name a general campaign, parent agency, or contractor, while later articles name a specific Super PAC, subsidiary agency, or specific perpetrator. If they describe the same real-world event or action against the same targets, return is_same_incident: true.
4. Coordinated Campaigns & Viral Hoax Trends: If two reports describe the same named viral AI hoax/meme trend or coordinated cyberattack wave unfolding across multiple locations within days of each other, return is_same_incident: true.
5. Return is_same_incident: false ONLY if they describe genuinely different lawsuits, different crimes, or distinct technical vulnerabilities—even if they involve the same company.
6. If is_same_incident is true, classify the evolution between the reports:
   - "evolution_type": "new_milestone" if Report B brings later developments, technical details, root causes, investigation updates, legal actions, or new dates. Use "redundant_copy" if Report B is virtually identical syndicate copy from the same time.
   - "milestone_phase": One of: "initial_report", "technical_disclosure", "impact_escalation", "investigation", "regulatory_action", "legal_settlement", "remediation", "follow_up".
   - "summary_delta": 1-2 concise sentences summarizing the NEW insight or development that Report B provides beyond Report A.

Respond strictly in valid JSON format:
{{
  "is_same_incident": true or false,
  "confidence": 0.95,
  "evolution_type": "new_milestone" or "redundant_copy",
  "milestone_phase": "technical_disclosure",
  "summary_delta": "Follow-up analysis reveals the breach occurred via...",
  "reasoning": "Short explanation focusing on whether the real-world event is identical."
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
                    client = genai.Client(
                        api_key=api_key,
                        http_options=types.HttpOptions(timeout=12000)
                    )
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                        )
                    )
                    if response and response.text:
                        text_clean = response.text.strip()
                        if text_clean.startswith("```json"):
                            text_clean = text_clean[7:]
                        if text_clean.endswith("```"):
                            text_clean = text_clean[:-3]
                        data = json.loads(text_clean.strip())
                        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                            data = data[0]
                        is_same = bool(data.get("is_same_incident", False))
                        confidence = float(data.get("confidence", 0.90))
                        reasoning = str(data.get("reasoning", ""))
                        m_info = {
                            "evolution_type": data.get("evolution_type", "new_milestone" if inc1.get("date") != inc2.get("date") else "redundant_copy"),
                            "milestone_phase": data.get("milestone_phase", "follow_up"),
                            "summary_delta": data.get("summary_delta", "")
                        }
                        _WORKING_DEDUP_MODEL = model_name
                        return is_same, confidence, reasoning, m_info
                except Exception as err:
                    err_str = str(err)
                    if any(code in err_str for code in ("429", "RESOURCE_EXHAUSTED", "Quota")):
                        time.sleep(1.0 * (attempt + 1))
                        continue
                    break

    return False, 0.0, "LLM call failed", default_milestone

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
            self.parent[root_j] = root_i

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
        is_same, confidence, reasoning, _ = verify_candidate_pair_llm(
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

def consolidate_new_against_existing(
    new_incidents: List[Dict[str, Any]],
    existing_incidents: List[Dict[str, Any]],
    api_key: Optional[str] = "",
    time_budget_sec: float = 60.0
) -> List[Dict[str, Any]]:
    """
    Ultra-Fast O(K) Incremental Deduplication Engine:
    - Pre-computes and caches TF-IDF vocabulary, IDF dictionary, and sparse vectors across
      all existing canonical records ONCE upfront in O(N).
    - Incrementally projects each newly ingested candidate incident in O(L) time.
    - Enforces a strict cumulative time budget (<= 60s) with deadline guardrails.
    - Filters candidate pairs with tightened threshold (effective_score >= 0.28 or shared entities).
    - If a new candidate describes an already known incident:
      -> Merges into the existing canonical incident: appends URLs to source_urls,
         merges affected_parties and damages, and PRESERVES the original incident_id and first date.
    - If a new candidate is truly novel:
      -> Assigns a new incident_id, appends to canonical catalog and updates cached vectors in O(1).
    - Zero quadratic O(N^2) loops over the historical dataset!
    """
    if not new_incidents:
        return existing_incidents

    start_time = time.time()
    deadline = start_time + float(time_budget_sec)
    effective_api_key = api_key or ""

    canonical_catalog = [dict(inc) for inc in existing_incidents]

    # Step 1: Pre-build index of exact URLs and titles from existing canonical records
    url_to_index: Dict[str, int] = {}
    title_to_index: Dict[str, int] = {}
    for idx, inc in enumerate(canonical_catalog):
        for u in get_normalized_url_set(inc):
            url_to_index[u] = idx
        norm_t = normalize_text(inc.get("title", ""))
        if norm_t:
            title_to_index[norm_t] = idx

    # Pre-compute TF-IDF vocabulary, document frequencies, IDF dictionary,
    # sparse vectors, and entity/scope metadata for all existing canonical catalog items ONCE upfront.
    canonical_corpus = [build_incident_corpus(inc) for inc in canonical_catalog]
    canonical_vectors, idf_dict, total_canonical_docs = build_tfidf_index(canonical_corpus)
    canonical_meta = [extract_incident_entity_metadata(inc) for inc in canonical_catalog]
    canonical_terms = [set(v.keys()) for v in canonical_vectors]

    llm_call_count = 0
    exact_match_count = 0
    merged_into_existing_count = 0
    newly_added_count = 0

    generic_parties = {
        "unknown", "public", "general public", "users", "consumers",
        "openai", "anthropic", "google", "microsoft", "meta", "xai", "deepseek"
    }

    for new_inc in new_incidents:
        new_urls = get_normalized_url_set(new_inc)
        exact_target_idx = None
        for u in new_urls:
            if u in url_to_index:
                exact_target_idx = url_to_index[u]
                break

        if exact_target_idx is None:
            norm_t = normalize_text(new_inc.get("title", ""))
            if norm_t and norm_t in title_to_index:
                exact_target_idx = title_to_index[norm_t]

        if exact_target_idx is not None:
            # Merge directly into existing canonical record (appends source_urls, preserves ID and original date)
            exact_milestone = {
                "evolution_type": "new_milestone" if new_inc.get("date") != canonical_catalog[exact_target_idx].get("date") else "redundant_copy",
                "milestone_phase": "follow_up" if (new_inc.get("date") or "") > (canonical_catalog[exact_target_idx].get("date") or "") else "initial_report",
                "summary_delta": (new_inc.get("summary") or "").strip().split(". ")[0] + ("." if not (new_inc.get("summary") or "").strip().endswith(".") else "")
            }
            canonical_catalog[exact_target_idx] = merge_duplicate_records(
                canonical_catalog[exact_target_idx], new_inc, milestone_info=exact_milestone
            )
            canonical_meta[exact_target_idx] = extract_incident_entity_metadata(canonical_catalog[exact_target_idx])
            for u in new_urls:
                url_to_index[u] = exact_target_idx
            exact_match_count += 1
            merged_into_existing_count += 1
            print(f"  [DEDUP EXACT MERGE] Appended source to '{canonical_catalog[exact_target_idx].get('incident_id')}' ({canonical_catalog[exact_target_idx].get('title')[:45]}...)")
            continue

        # Step 2: Incremental vector projection of new_inc against pre-computed IDF dictionary
        new_corpus = build_incident_corpus(new_inc)
        new_vec = vectorize_single_document(new_corpus, idf_dict, total_canonical_docs)
        new_meta = extract_incident_entity_metadata(new_inc)
        new_terms = set(new_vec.keys())

        # Collect candidate matches with effective_score >= 0.28 or shared entities
        candidates = []
        for idx, inc in enumerate(canonical_catalog):
            target_terms = canonical_terms[idx]
            if new_terms.isdisjoint(target_terms):
                sim = 0.0
            else:
                sim = cosine_similarity_vectors(new_vec, canonical_vectors[idx])

            target_meta = canonical_meta[idx]

            # Fast gating: skip full boost computation if similarity is negligible and no entity overlap
            if (
                sim < 0.08
                and not (new_meta["parties"] & target_meta["parties"])
                and not (new_meta["tokens"] & target_meta["tokens"])
                and not (new_meta["long_tokens"] & target_meta["words"])
                and not (target_meta["long_tokens"] & new_meta["words"])
            ):
                boost, shared_entities = 0.0, set()
            else:
                boost, shared_entities = compute_boost_from_metadata(new_meta, target_meta)

            effective_score = sim + boost

            if effective_score >= 0.28 or len(shared_entities) > 0:
                candidates.append((effective_score, idx, inc))

        # Sort candidates descending by effective score
        candidates.sort(key=lambda c: c[0], reverse=True)

        merged = False
        # Step 3: Targeted LLM verification on Top candidate matches within time budget
        if effective_api_key:
            for eff_score, idx, candidate_inc in candidates[:2]:
                # Strict deadline check before every LLM call (treat unverified candidates safely as novel records)
                remaining_time = deadline - time.time()
                if remaining_time <= 0.0 or (time_budget_sec > 5.0 and remaining_time < 3.0):
                    print(f"  [DEDUP TIMEOUT SAFEGUARD] Approaching cumulative deadline ({remaining_time:.1f}s remaining). Skipping further LLM checks.")
                    break

                is_same, confidence, reasoning, milestone_info = verify_candidate_pair_llm(
                    candidate_inc, new_inc, api_key=effective_api_key
                )
                llm_call_count += 1
                print(f"  [DEDUP LLM VERIFY] Candidate '{candidate_inc.get('incident_id')}' (Score: {eff_score:.2f}) vs New: Match={is_same} ({confidence:.2f}) | {reasoning}")

                if is_same and confidence >= 0.70:
                    canonical_catalog[idx] = merge_duplicate_records(
                        candidate_inc, new_inc, milestone_info=milestone_info
                    )
                    canonical_meta[idx] = extract_incident_entity_metadata(canonical_catalog[idx])
                    for u in new_urls:
                        url_to_index[u] = idx
                    merged_into_existing_count += 1
                    merged = True
                    print(f"  [DEDUP LLM MERGE] Merged new report into existing '{candidate_inc.get('incident_id')}' ({candidate_inc.get('title')[:45]}...)")
                    break

        if merged:
            continue

        # Step 4: Truly novel incident -> Assign ID, add to catalog, and update cached vectors in O(1)
        if not new_inc.get("incident_id"):
            date_prefix = (new_inc.get("date") or datetime.now().strftime("%Y-%m-%d")).replace("-", "")
            seq_num = len(canonical_catalog) + 1
            new_inc["incident_id"] = f"INC-{date_prefix}-{seq_num:03d}"

        new_idx = len(canonical_catalog)
        canonical_catalog.append(new_inc)
        canonical_vectors.append(new_vec)
        canonical_meta.append(new_meta)
        canonical_terms.append(new_terms)
        total_canonical_docs += 1
        for u in new_urls:
            url_to_index[u] = new_idx
        norm_t = normalize_text(new_inc.get("title", ""))
        if norm_t:
            title_to_index[norm_t] = new_idx
        newly_added_count += 1
        print(f"  [DEDUP NEW CANONICAL] Added novel incident '{new_inc.get('incident_id')}' ({new_inc.get('title')[:45]}...)")

    print(f"\n[INCREMENTAL DEDUP TELEMETRY] Evaluated: {len(new_incidents)} | Merged: {merged_into_existing_count} (Exact: {exact_match_count}) | New: {newly_added_count} | LLM Calls: {llm_call_count}")
    return canonical_catalog

