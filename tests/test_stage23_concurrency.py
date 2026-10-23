"""
Empirical Adversarial Stress Tests: Stage 2 & Stage 3 Concurrency, Thread Safety & Backoff
Target: scripts/ingest.py (process_candidates_concurrently, stage2_binary_gatekeeper, stage3_extract_taxonomy)
100% self-contained: 0 network requests, 0 real API keys required.
"""

import unittest
from unittest.mock import patch, MagicMock
import time
import threading
import concurrent.futures
from typing import Dict, Any, List

from scripts.ingest import (
    process_candidates_concurrently,
    stage2_binary_gatekeeper,
    stage3_extract_taxonomy,
    PREFERRED_MODELS_STAGE2,
    PREFERRED_MODELS_STAGE3,
    _WORKING_MODEL_LOCK,
)
import scripts.ingest as ingest_mod


class TestStage23ConcurrencyAndBackoff(unittest.TestCase):

    def setUp(self):
        # Reset working model state before each test
        with _WORKING_MODEL_LOCK:
            ingest_mod._WORKING_MODEL_STAGE2 = None
            ingest_mod._WORKING_MODEL_STAGE3 = None

    def tearDown(self):
        # Clean up working model state after each test
        with _WORKING_MODEL_LOCK:
            ingest_mod._WORKING_MODEL_STAGE2 = None
            ingest_mod._WORKING_MODEL_STAGE3 = None

    # -------------------------------------------------------------------------
    # TEST 1: Concurrency Speedup in process_candidates_concurrently
    # -------------------------------------------------------------------------
    def test_process_candidates_concurrently_speedup(self):
        """
        Adversarial Concurrency Benchmark:
        Verifies that evaluating 10 candidates with 100ms artificial delay each
        using 4 workers executes in ~300ms (wave: 4 + 4 + 2 items = ~300ms),
        demonstrating significant concurrent speedup vs 1000ms serial execution.
        """
        # --- ARRANGE ---
        num_candidates = 10
        simulated_delay = 0.100  # 100ms
        candidates = [
            {
                "title": f"Autonomous AI Breach Incident #{i}",
                "link": f"https://example.com/incident-{i}",
                "pub_date_clean": "2026-10-23",
                "scraped_title": f"Autonomous AI Breach Incident #{i}",
                "scraped_text": f"Detailed operational report of breach incident #{i} involving rogue agents.",
                "source_type": "google_news_rss"
            }
            for i in range(num_candidates)
        ]

        def mock_process_article(cand, api_key):
            time.sleep(simulated_delay)
            return {
                "incident_id": f"ai-incident-{cand['link'].split('-')[-1]}",
                "title": cand["title"],
                "date": cand["pub_date_clean"],
                "source_urls": [cand["link"]],
                "financial_damage_usd": 150000.0,
                "impact_scope": "discrete_incident"
            }

        # --- ACT ---
        # 1. Baseline serial duration
        t_serial_start = time.perf_counter()
        for cand in candidates:
            mock_process_article(cand, api_key="test-api-key")
        dur_serial = time.perf_counter() - t_serial_start

        # 2. Concurrent execution with 4 workers
        with patch("scripts.ingest.process_article_3stage_pipeline", new=mock_process_article):
            t_conc_start = time.perf_counter()
            results = process_candidates_concurrently(candidates, api_key="test-api-key", max_workers=4)
            dur_conc = time.perf_counter() - t_conc_start

        # --- ASSERT ---
        self.assertEqual(len(results), num_candidates, "All 10 candidates must be successfully processed.")
        
        speedup = dur_serial / max(dur_conc, 0.001)
        print(f"\n  [BENCHMARK] 10 items: Serial={dur_serial*1000:.1f}ms vs 4-Worker={dur_conc*1000:.1f}ms (Speedup: {speedup:.2f}x)")
        
        self.assertLess(
            dur_conc, 
            0.85, 
            f"Concurrent execution time {dur_conc:.3f}s was too slow for 4 workers (expected ~0.30s-0.45s)."
        )
        self.assertGreater(
            speedup, 
            1.8, 
            f"Concurrency speedup {speedup:.2f}x is below the expected minimum 1.8x threshold."
        )

    # -------------------------------------------------------------------------
    # TEST 2: Thread-Safety of _WORKING_MODEL_STAGE2 and _WORKING_MODEL_STAGE3
    # -------------------------------------------------------------------------
    def test_thread_safe_working_model_updates(self):
        """
        Stress-tests concurrent reads and updates to _WORKING_MODEL_STAGE2 & _WORKING_MODEL_STAGE3
        under high thread contention (16 threads across 48 tasks), ensuring zero race conditions
        or memory corruption.
        """
        # --- ARRANGE ---
        num_tasks = 48
        errors = []

        def mock_generate_content(model, contents, config=None):
            # Simulate slight thread interleaving
            time.sleep(0.005)
            mock_resp = MagicMock()
            if model in PREFERRED_MODELS_STAGE2:
                mock_resp.text = '{"is_ai_incident": true, "confidence": 0.95, "rejection_reason": ""}'
            else:
                mock_resp.text = '{"title": "Test Incident", "system_classification": "Autonomous Agent"}'
            return mock_resp

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = mock_generate_content

        def worker_task(idx: int):
            try:
                if idx % 2 == 0:
                    res = stage2_binary_gatekeeper(f"Title {idx}", f"Text {idx}", api_key="dummy-key")
                    if not res.get("is_ai_incident"):
                        errors.append(f"Stage 2 failed for task {idx}")
                else:
                    res = stage3_extract_taxonomy(f"Title {idx}", f"Text {idx}", api_key="dummy-key")
                    if not res or not isinstance(res, dict):
                        errors.append(f"Stage 3 failed for task {idx}")
            except Exception as e:
                errors.append(f"Task {idx} raised unexpected exception: {e}")

        # --- ACT ---
        with patch("scripts.ingest.get_thread_genai_client", return_value=mock_client), \
             patch("scripts.ingest.HAS_GENAI", True):
            with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
                futures = [executor.submit(worker_task, i) for i in range(num_tasks)]
                concurrent.futures.wait(futures)

        # --- ASSERT ---
        self.assertEqual(len(errors), 0, f"Thread contention produced errors: {errors}")
        with _WORKING_MODEL_LOCK:
            s2_model = ingest_mod._WORKING_MODEL_STAGE2
            s3_model = ingest_mod._WORKING_MODEL_STAGE3

        self.assertIn(
            s2_model, 
            PREFERRED_MODELS_STAGE2, 
            f"_WORKING_MODEL_STAGE2 corrupt or invalid: {s2_model}"
        )
        self.assertIn(
            s3_model, 
            PREFERRED_MODELS_STAGE3, 
            f"_WORKING_MODEL_STAGE3 corrupt or invalid: {s3_model}"
        )

    # -------------------------------------------------------------------------
    # TEST 3: Rate-Limit Backoff (429) & Hierarchy Fallback in Stage 2
    # -------------------------------------------------------------------------
    def test_stage2_rate_limit_backoff_and_hierarchy_fallback(self):
        """
        Simulates 429 RESOURCE_EXHAUSTED errors on primary model (gemma-4-26b-a4b-it).
        Verifies:
        1. Full-jitter exponential backoff handles retries on primary model.
        2. Clean fallback to secondary model (gemma-4-31b-it) in the hierarchy.
        3. _WORKING_MODEL_STAGE2 is updated to the secondary model upon success.
        """
        # --- ARRANGE ---
        primary_model = PREFERRED_MODELS_STAGE2[0]    # 'gemma-4-26b-a4b-it'
        secondary_model = PREFERRED_MODELS_STAGE2[1]  # 'gemma-4-31b-it'
        
        sleep_durations = []
        models_called = []

        def spy_sleep(seconds):
            sleep_durations.append(seconds)

        def mock_generate_content(model, contents, config=None):
            models_called.append(model)
            if model == primary_model:
                raise Exception("429 RESOURCE_EXHAUSTED: Rate limit exceeded. Please retry later.")
            elif model == secondary_model:
                resp = MagicMock()
                resp.text = '{"is_ai_incident": true, "confidence": 0.98, "rejection_reason": ""}'
                return resp
            raise Exception("Unexpected model invoked")

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = mock_generate_content

        # --- ACT ---
        with patch("scripts.ingest.get_thread_genai_client", return_value=mock_client), \
             patch("scripts.ingest.HAS_GENAI", True), \
             patch("time.sleep", side_effect=spy_sleep):
            result = stage2_binary_gatekeeper(
                title="Rogue AI Financial Trading Incident",
                text="Autonomous algorithmic agent caused market dislocation and $10M loss.",
                api_key="valid-mock-key"
            )

        # --- ASSERT ---
        self.assertTrue(result["is_ai_incident"], "Gatekeeper should succeed on secondary model.")
        self.assertEqual(result["confidence"], 0.98)

        # Verify retry count: primary model attempted 3 times with 3 backoff sleeps
        primary_attempts = [m for m in models_called if m == primary_model]
        secondary_attempts = [m for m in models_called if m == secondary_model]
        self.assertEqual(len(primary_attempts), 3, "Primary model should be attempted 3 times.")
        self.assertEqual(len(secondary_attempts), 1, "Secondary model should be called once.")
        self.assertEqual(len(sleep_durations), 3, "Exactly 3 retry sleeps should be recorded.")

        # Verify full-jitter exponential backoff formula: (1.5 ** attempt) + uniform(0.5, 1.5)
        # Attempt 0: 1.0 + [0.5, 1.5] = [1.5, 2.5]
        # Attempt 1: 1.5 + [0.5, 1.5] = [2.0, 3.0]
        # Attempt 2: 2.25 + [0.5, 1.5] = [2.75, 3.75]
        self.assertTrue(1.5 <= sleep_durations[0] <= 2.5, f"Sleep 0 {sleep_durations[0]} outside [1.5, 2.5]")
        self.assertTrue(2.0 <= sleep_durations[1] <= 3.0, f"Sleep 1 {sleep_durations[1]} outside [2.0, 3.0]")
        self.assertTrue(2.75 <= sleep_durations[2] <= 3.75, f"Sleep 2 {sleep_durations[2]} outside [2.75, 3.75]")

        # Verify cached working model was switched to secondary model
        with _WORKING_MODEL_LOCK:
            self.assertEqual(ingest_mod._WORKING_MODEL_STAGE2, secondary_model)

    # -------------------------------------------------------------------------
    # TEST 4: Rate-Limit Backoff (429) & Hierarchy Fallback in Stage 3
    # -------------------------------------------------------------------------
    def test_stage3_rate_limit_backoff_and_hierarchy_fallback(self):
        """
        Simulates 429 RESOURCE_EXHAUSTED errors on Stage 3 primary model (gemini-3.8-flash).
        Verifies:
        1. Clean retry backoff on gemini-3.8-flash.
        2. Fallback to gemini-3.6-flash.
        3. Proper taxonomy JSON parsing and working model update.
        """
        # --- ARRANGE ---
        primary_model = PREFERRED_MODELS_STAGE3[0]    # 'gemini-3.8-flash'
        secondary_model = PREFERRED_MODELS_STAGE3[1]  # 'gemini-3.6-flash'
        
        sleep_durations = []
        models_called = []

        def spy_sleep(seconds):
            sleep_durations.append(seconds)

        def mock_generate_content(model, contents, config=None):
            models_called.append(model)
            if model == primary_model:
                raise Exception("429 Quota exceeded for model gemini-3.8-flash: RESOURCE_EXHAUSTED")
            elif model == secondary_model:
                resp = MagicMock()
                resp.text = '''```json
                {
                    "title": "Autonomous AI Agent Compromised Cloud Database",
                    "summary": "Agent leaked AWS keys leading to unauthorized data dump.",
                    "system_classification": "Autonomous Agent",
                    "harm_domain": "Security & Privacy",
                    "financial_damage_reported": "$500,000",
                    "affected_entities": ["Acme Corp"]
                }
                ```'''
                return resp
            raise Exception("Unexpected model invoked")

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = mock_generate_content

        # --- ACT ---
        with patch("scripts.ingest.get_thread_genai_client", return_value=mock_client), \
             patch("scripts.ingest.HAS_GENAI", True), \
             patch("time.sleep", side_effect=spy_sleep):
            result = stage3_extract_taxonomy(
                title="Autonomous AI Agent Compromised Cloud Database",
                text="Agent leaked AWS keys leading to unauthorized data dump.",
                api_key="valid-mock-key"
            )

        # --- ASSERT ---
        self.assertIsNotNone(result, "Stage 3 must return taxonomy data after secondary fallback.")
        self.assertEqual(result["system_classification"], "Autonomous Agent")
        self.assertEqual(models_called.count(primary_model), 3)
        self.assertEqual(models_called.count(secondary_model), 1)
        self.assertEqual(len(sleep_durations), 3)

        with _WORKING_MODEL_LOCK:
            self.assertEqual(ingest_mod._WORKING_MODEL_STAGE3, secondary_model)

    # -------------------------------------------------------------------------
    # TEST 5: Subsequent Invocations Prioritize Working Model
    # -------------------------------------------------------------------------
    def test_working_model_prioritized_on_subsequent_calls(self):
        """
        Verifies that once a model succeeds and becomes _WORKING_MODEL_STAGE2,
        subsequent invocations try that working model first without re-attempting
        failing models at the head of the static list.
        """
        # --- ARRANGE ---
        # Set working model to index 2 ('gemini-3.6-flash')
        working_model = PREFERRED_MODELS_STAGE2[2]
        with _WORKING_MODEL_LOCK:
            ingest_mod._WORKING_MODEL_STAGE2 = working_model

        models_called = []
        def mock_generate_content(model, contents, config=None):
            models_called.append(model)
            resp = MagicMock()
            resp.text = '{"is_ai_incident": true, "confidence": 0.90, "rejection_reason": ""}'
            return resp

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = mock_generate_content

        # --- ACT ---
        with patch("scripts.ingest.get_thread_genai_client", return_value=mock_client), \
             patch("scripts.ingest.HAS_GENAI", True):
            stage2_binary_gatekeeper("Title", "Text", api_key="dummy-key")

        # --- ASSERT ---
        self.assertEqual(len(models_called), 1)
        self.assertEqual(models_called[0], working_model, "Working model must be tried first.")

    # -------------------------------------------------------------------------
    # TEST 6: Non-Retryable Error Immediately Advances Model Without Jitter Delay
    # -------------------------------------------------------------------------
    def test_non_retryable_error_does_not_waste_jitter_sleeps(self):
        """
        Verifies that non-transient errors (e.g. 400 Bad Request) do not waste
        retry attempts or jitter sleeps, and immediately advance to the next model.
        """
        # --- ARRANGE ---
        primary_model = PREFERRED_MODELS_STAGE2[0]
        secondary_model = PREFERRED_MODELS_STAGE2[1]

        sleep_calls = []
        models_called = []

        def mock_generate_content(model, contents, config=None):
            models_called.append(model)
            if model == primary_model:
                raise Exception("400 Bad Request: Invalid model argument or malformed request.")
            elif model == secondary_model:
                resp = MagicMock()
                resp.text = '{"is_ai_incident": false, "confidence": 0.99, "rejection_reason": "Not an incident"}'
                return resp
            raise Exception("Unexpected model invoked")

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = mock_generate_content

        # --- ACT ---
        with patch("scripts.ingest.get_thread_genai_client", return_value=mock_client), \
             patch("scripts.ingest.HAS_GENAI", True), \
             patch("time.sleep", side_effect=sleep_calls.append):
            result = stage2_binary_gatekeeper("Title", "Text", api_key="dummy-key")

        # --- ASSERT ---
        self.assertEqual(len(sleep_calls), 0, "Non-transient 400 error must not trigger retry sleep.")
        self.assertEqual(models_called.count(primary_model), 1, "Primary model should only be tried once on 400.")
        self.assertEqual(models_called.count(secondary_model), 1)
        self.assertFalse(result["is_ai_incident"])

    # -------------------------------------------------------------------------
    # TEST 7: Total Quota Exhaustion Fails Gracefully Without Crashing
    # -------------------------------------------------------------------------
    def test_total_quota_exhaustion_fails_gracefully(self):
        """
        Adversarial Edge Case:
        All models in Stage 2 hierarchy return 429 Quota Exhausted.
        Verifies pipeline fails safely and gracefully, returning default rejection
        without unhandled exceptions.
        """
        # --- ARRANGE ---
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED across all models")

        # --- ACT ---
        with patch("scripts.ingest.get_thread_genai_client", return_value=mock_client), \
             patch("scripts.ingest.HAS_GENAI", True), \
             patch("time.sleep"):  # No-op sleep for fast execution
            result = stage2_binary_gatekeeper("Title", "Text", api_key="dummy-key")

        # --- ASSERT ---
        self.assertIsInstance(result, dict)
        self.assertFalse(result["is_ai_incident"])
        self.assertIn("LLM Gatekeeper execution error", result["rejection_reason"])

    # -------------------------------------------------------------------------
    # TEST 8: Error Isolation in process_candidates_concurrently
    # -------------------------------------------------------------------------
    def test_process_candidates_concurrently_error_isolation(self):
        """
        Verifies that an unhandled exception or parsing failure on a single candidate
        is cleanly caught and isolated, allowing other concurrent candidates to succeed.
        """
        # --- ARRANGE ---
        candidates = [
            {"title": "Good Incident 1", "link": "https://example.com/1"},
            {"title": "Exploding Incident 2", "link": "https://example.com/2"},
            {"title": "Good Incident 3", "link": "https://example.com/3"},
        ]

        def mock_process_article(cand, api_key):
            if "Exploding" in cand["title"]:
                raise RuntimeError("Catastrophic downstream parse explosion!")
            return {"incident_id": f"id-{cand['link']}", "title": cand["title"]}

        # --- ACT ---
        with patch("scripts.ingest.process_article_3stage_pipeline", side_effect=mock_process_article):
            results = process_candidates_concurrently(candidates, api_key="dummy-key", max_workers=3)

        # --- ASSERT ---
        self.assertEqual(len(results), 2, "Only the 2 healthy candidates should be returned.")
        titles = [r["title"] for r in results]
        self.assertIn("Good Incident 1", titles)
        self.assertIn("Good Incident 3", titles)


if __name__ == "__main__":
    unittest.main()
