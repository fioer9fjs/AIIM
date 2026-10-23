"""
Empirical Stress Test Suite for Milestone 2: Deduplication Engine Optimization.
Tests:
1. Time Budget Enforcement: Strict deadline halting when LLM verification calls sleep 1.0s with time_budget_sec=2.0.
2. Mathematical Equivalence: Numerical precision between cached vectorize_single_document vs compute_tfidf_vectors.
3. Real-World Performance Benchmark: Incremental projection of 40 candidate incidents against 351 canonical incidents (<1.5s).
"""

import unittest
import time
import json
import os
from unittest.mock import patch
from typing import List, Dict, Any

from scripts.dedup_engine import (
    build_incident_corpus,
    compute_tfidf_vectors,
    build_tfidf_index,
    vectorize_single_document,
    cosine_similarity_vectors,
    consolidate_new_against_existing
)

class TestM2EmpiricalStress(unittest.TestCase):

    def setUp(self):
        # Load canonical incidents from dataset
        incidents_path = os.path.join(os.path.dirname(__file__), "..", "src", "data", "incidents.json")
        with open(incidents_path, "r", encoding="utf-8") as f:
            self.incidents = json.load(f)

    def test_mathematical_equivalence_vectorization(self):
        """
        Compares cosine similarities of candidate documents computed via cached
        vectorize_single_document against full batch compute_tfidf_vectors across 50 text pairs.
        Verifies max difference is strictly < 1e-5.
        """
        # --- ARRANGE ---
        corpora = [build_incident_corpus(inc) for inc in self.incidents[:100]]
        batch_vectors, idf_index = compute_tfidf_vectors(corpora)

        # --- ACT & ASSERT ---
        max_diff = 0.0
        for k in range(50):
            doc1 = corpora[2 * k]
            doc2 = corpora[2 * k + 1]

            sim_batch = cosine_similarity_vectors(batch_vectors[2 * k], batch_vectors[2 * k + 1])

            vec1_single = vectorize_single_document(doc1, idf_index, len(corpora))
            vec2_single = vectorize_single_document(doc2, idf_index, len(corpora))
            sim_single = cosine_similarity_vectors(vec1_single, vec2_single)

            diff = abs(sim_batch - sim_single)
            if diff > max_diff:
                max_diff = diff

        print(f"\n[EMPIRICAL TEST 1] Max Cosine Similarity Diff across 50 pairs: {max_diff:.10e}")
        self.assertLess(max_diff, 1e-5, f"Mathematical divergence exceeded 1e-5: {max_diff}")

    def test_time_budget_enforcement_and_safe_novelty(self):
        """
        Simulates slow LLM responses (1.0s sleep per call).
        With 10 candidate articles and time_budget_sec=2.0, execution must strictly
        halt at ~2.0s without hanging, making at least 1-2 calls before deadline,
        and safely save remaining unverified articles as novel records.
        """
        # --- ARRANGE ---
        existing = [
            {
                "incident_id": "INC-ANCHOR-001",
                "title": "Autonomous Drone Fleet Navigation Failure in Metropolitan Area",
                "summary": "An autonomous delivery drone fleet suffered widespread navigational failure.",
                "date": "2026-10-20",
                "affected_parties": ["SkyRoute Logistics", "AeroNav AI"],
                "source_urls": ["https://news.example.com/drone-anchor"]
            }
        ]

        candidates = [
            {
                "title": f"Autonomous Drone Navigation Failure Follow-up Report #{i}",
                "summary": f"Further analysis of the drone fleet navigation failure incident in sector {i}.",
                "date": "2026-10-21",
                "affected_parties": ["SkyRoute Logistics", "AeroNav AI"],
                "source_urls": [f"https://news.example.com/drone-candidate-{i}"]
            }
            for i in range(10)
        ]

        call_count = 0
        def mock_verify_slow(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            time.sleep(1.0)
            return False, 0.0, "Different incident", {}

        # --- ACT ---
        t0 = time.time()
        with patch("scripts.dedup_engine.verify_candidate_pair_llm", side_effect=mock_verify_slow):
            result = consolidate_new_against_existing(
                candidates,
                existing,
                api_key="mock-key",
                time_budget_sec=2.0
            )
        elapsed = time.time() - t0

        print(f"\n[EMPIRICAL TEST 2] Time Budget Test: elapsed={elapsed:.3f}s, LLM calls={call_count}, total records={len(result)}")

        # --- ASSERT ---
        # 1. Total records must be 11 (1 anchor + 10 candidates safely added as novel)
        self.assertEqual(len(result), 11, "All candidates must be safely preserved as novel records upon timeout.")
        
        # 2. Must not hang
        self.assertLess(elapsed, 4.0, f"Execution hung or exceeded safety bounds: {elapsed:.2f}s")

        # 3. Time budget must allow calls up to budget (~2.0s, at least 1-2 calls), not abort at 0.0s
        self.assertGreaterEqual(call_count, 1, f"Time budget aborted prematurely at t=0s without making any calls (call_count={call_count})")
        self.assertGreaterEqual(elapsed, 1.0, f"Execution exited prematurely before time budget: {elapsed:.3f}s")

    def test_real_world_performance_benchmark(self):
        """
        Incremental projection of 40 candidates against 351 canonical incidents in incidents.json.
        Acceptance criteria: total time < 1.5s (<60s requirement).
        """
        # --- ARRANGE ---
        canonical = [dict(x) for x in self.incidents]
        candidates = [
            {
                "title": f"Novel AI Safety Benchmark Failure #{i} in Cloud Inference",
                "summary": f"Independent auditors detected model safety degradation in benchmark run #{i}.",
                "date": "2026-10-23",
                "affected_parties": [f"Lab_{i}"],
                "geographic_scope": ["global"],
                "source_urls": [f"https://news.example.com/safety-incident-{i}"]
            }
            for i in range(40)
        ]

        # --- ACT ---
        t0 = time.time()
        result = consolidate_new_against_existing(
            candidates,
            canonical,
            api_key="",
            time_budget_sec=60.0
        )
        elapsed = time.time() - t0

        print(f"\n[EMPIRICAL TEST 3] Real-world benchmark: 40 candidates vs {len(canonical)} canonical: elapsed={elapsed:.3f}s")

        # --- ASSERT ---
        self.assertEqual(len(result), len(canonical) + 40)
        self.assertLess(elapsed, 1.5, f"Incremental projection took {elapsed:.3f}s, exceeding 1.5s benchmark ceiling!")

if __name__ == "__main__":
    unittest.main()
