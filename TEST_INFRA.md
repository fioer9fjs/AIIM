# E2E Test Infra: AI Incident Monitor Pipeline Optimization

## Test Philosophy
- Opaque-box, requirement-driven, deterministic. No dependency on implementation internals.
- Verification covers:
  - Scraping performance & bounded timeouts (hard 4.0s ceiling, connect=1.5s, read=2.5s)
  - SSRF protection preservation (`safe_requests_get`)
  - Stage 2 & 3 LLM pipeline concurrency, rate-limit backoff, and model hierarchy
  - Incremental deduplication speedup, TF-IDF indexing, and strict 60s time-budget bounds
  - 100% pass of existing 91 unit tests
  - TypeScript build cleanliness (`npx tsc --noEmit` and `npm run build`)

## Feature Inventory
| # | Feature | Source (requirement) | Tier 1 | Tier 2 | Tier 3 |
|---|---------|---------------------|:------:|:------:|:------:|
| 1 | Bounded Safe HTTP Scraping | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 2 | Cached & Bounded URL Decoding | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 3 | Eliminate Recursive Fallback | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 4 | Concurrent Batch Scraping | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 5 | Stage 3 Model Hierarchy | GEMINI.md | 5 | 5 | ✓ |
| 6 | Bounded LLM Timeouts & Jitter Backoff | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 7 | Concurrent LLM Candidate Pool | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 8 | Pre-computed TF-IDF Caching | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 9 | Bounded Semantic LLM Verification | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |

## Test Architecture
- Test runner: `python -m unittest discover -s tests -p "test_*.py" -v`
- Pass/fail semantics: 0 errors, 0 failures, exit code 0
- Frontend build check: `npx tsc --noEmit` and `npm run build`
- Directory layout:
  - `tests/test_ingest_pipeline.py`
  - `tests/test_dedup_engine.py`
  - `tests/test_security.py`

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Full batch ingestion with 40 harvested URLs | Scraping, Concurrency, Deduplication | High |
| 2 | Unresponsive / hanging URL handling | Bounded timeouts, SSRF safety | Medium |
| 3 | Heavy duplicate candidate batch against 351 existing records | TF-IDF caching, 60s time budget | High |
