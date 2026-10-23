# Project: AI Incident Monitor Pipeline Redesign & Optimization

## Architecture
The Global AI Incident Monitor ingestion pipeline automatically harvests, scrapes, classifies, deduplicates, and stores real-world AI incidents.
The pipeline operates in sequential stages:
1. **Stage 1 (Harvesting)**: Multi-lane RSS harvesting (Google News RSS with query length <= 160 chars, ArXiv, AIID, GDELT BigQuery).
2. **Stage 1.5 (High-Throughput Concurrent Scraping)**: Decoupled concurrent web scraping (`batch_scrape_candidates`) with bounded per-host timeouts (connect 1.5s, read 2.5s, hard 4.0s ceiling), thread-local sessions, connection pooling, and cached Google News URL decoding.
3. **Stage 2 & 3 (Concurrent LLM Pipeline)**: Concurrent candidate evaluation (`ThreadPoolExecutor(max_workers=4)`) for binary gatekeeper classification and 7-layer taxonomy extraction, enforcing GEMINI.md model hierarchy, bounded API timeouts, full-jitter backoff, and thread-safe model caching.
4. **Stage 4 (Bounded O(K) Incremental Deduplication)**: Pre-computed and cached TF-IDF vectorization across existing canonical records, candidate scoring, and time-budgeted semantic LLM verification (max 60s cumulative budget, 8s per-call timeout, score >= 0.28).
5. **Stage 5 (Persistence & Sync)**: Local JSON persistence (`src/data/incidents.json`) and Supabase PostgreSQL synchronization using `SUPABASE_SECRET_KEY`.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Bounded Safe HTTP Scraping | Add 4.0s hard ceiling, max 2 redirects, connect=1.5s/read=2.5s timeout, thread-local requests.Session with connection pooling | M1 | Survey R1 |
| 2 | Cached & Bounded URL Decoding | In-memory cache `_URL_DECODE_CACHE` + 2.5s worker timeout wrapper for `googlenewsdecoder` | M1 | Survey R1 |
| 3 | Eliminate Recursive Fallback | Remove Tier 3 recursive Google News search fallback from `fetch_full_text_and_title`; cap GDELT alternate domain fallback to 1 domain | M1 | Survey R1 |
| 4 | Concurrent Batch Scraping | `batch_scrape_candidates(candidates, max_workers=16)` executing right after URL filtering, populating `scraped_title` and `scraped_text` | M1 | Survey R1 |
| 5 | GEMINI.md Stage 3 Hierarchy Alignment | Align `PREFERRED_MODELS_STAGE3` to `["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemma-4-31b-it"]` | M1 | Survey R2 |
| 6 | Bounded LLM Timeouts & Jitter Backoff | Add `http_options=types.HttpOptions(timeout=15000/25000)` and full-jitter backoff `(1.5**attempt) + uniform(0.5, 1.5)` | M1 | Survey R2 |
| 7 | Concurrent LLM Candidate Pool | `process_candidates_concurrently` using `ThreadPoolExecutor(max_workers=4)` with thread-safe lock for `_WORKING_MODEL_STAGE2/3` and thread-local client | M1 | Survey R2 |
| 8 | Pre-computed TF-IDF Caching | Pre-compute and cache IDF vocabulary and sparse vectors across existing canonical records in `consolidate_new_against_existing` | M2 | Survey R3 |
| 9 | Bounded Semantic LLM Verification | Time-budgeted LLM verification (cumulative <= 60s, deadline check, 8s per-call timeout, score >= 0.28 threshold) | M2 | Survey R3 |
| 10 | Regression & Concurrency Unit Testing | Add mocked offline unit tests in `tests/test_ingest_pipeline.py` and `tests/test_dedup_engine.py` covering concurrency, timeouts, and dedup budgets | M3 | Survey R2/R3 |
| 11 | Full Suite Validation & TypeScript Build | Verify all 91+ unit tests pass and `npx tsc --noEmit` / `npm run build` succeed | M3 | Survey R4 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Ingestion Pipeline Optimization (Scraping & LLM) | `scripts/ingest.py`: Bounded safe HTTP scraping, cached URL decoding, remove recursive search fallback, batch scraping, Stage 3 model hierarchy alignment, concurrent LLM candidate pool, bounded timeouts & jitter backoff | none | DONE |
| M2 | Deduplication Engine Optimization (TF-IDF & Time Budget) | `scripts/dedup_engine.py`: Pre-computed TF-IDF vocabulary and vector caching, candidate filter threshold tightening, cumulative 60s time budget with deadline check & 8s client timeout | none | DONE |
| M3 | Comprehensive Test Hardening & Final Validation | `tests/`: Concurrency & timeout unit tests, full 91+ unit test suite pass, TypeScript build verification, adversarial coverage check, forensic audit | M1, M2 | DONE |

## Interface Contracts
### `scripts/ingest.py` (Scraping) ↔ `scripts/ingest.py` (LLM Pipeline)
- `batch_scrape_candidates(candidates: List[Dict[str, Any]], max_workers: int = 16) -> List[Dict[str, Any]]`:
  - Enriches each candidate dict with `"scraped_title"`: str and `"scraped_text"`: str.
  - Leaves candidate metadata intact.
- `fetch_full_text_and_title(url: str, reported_by_samples: List[str] = None, search_title: str = "") -> Dict[str, str]`:
  - Retains synchronous signature returning `{"title": str, "full_text": str}` to preserve 100% test compatibility.

### `scripts/ingest.py` (Harvest/Scrape/LLM) ↔ `scripts/dedup_engine.py` (Deduplication)
- `consolidate_new_against_existing(new_incidents: List[Dict], existing_incidents: List[Dict], api_key: str = None, time_budget_sec: float = 60.0) -> Tuple[List[Dict], List[Dict]]`:
  - Accepts candidate new incidents and existing canonical records.
  - Returns `(merged_canonical_catalog, newly_added_incidents)`.
  - Enforces `time_budget_sec <= 60.0`.

## Code Layout
- `scripts/ingest.py`: Harvesting, URL decoding, web scraping, Stage 2 Gatekeeper, Stage 3 Taxonomy Extractor, candidate loop orchestration.
- `scripts/dedup_engine.py`: Deduplication engine, TF-IDF vectorization, candidate pair verification, canonical catalog consolidation.
- `tests/test_ingest_pipeline.py`: Unit tests for ingestion pipeline, SSRF safety, scraping, and LLM stages.
- `tests/test_dedup_engine.py`: Unit tests for deduplication, TF-IDF, clustering, and incremental consolidation.
- `src/data/incidents.json`: Canonical dataset storage.
