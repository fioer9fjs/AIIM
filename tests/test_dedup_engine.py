"""
Unit Tests for Deduplication Engine (scripts/dedup_engine.py)
Following the strict Arrange - Act - Assert (AAA) pattern.
100% self-contained: 0 external network requests, 0 API tokens required.
"""

import unittest
from scripts.dedup_engine import (
    UnionFind,
    normalize_url,
    normalize_text,
    get_normalized_url_set,
    is_exact_duplicate,
    merge_duplicate_records,
    tokenize,
    compute_tfidf_vectors,
    cosine_similarity_vectors,
    compute_candidate_pairs_tfidf,
)


class TestUnionFind(unittest.TestCase):
    """
    Unit Tests focusing on edge cases, boundary values, and regression testing for UnionFind.
    """

    def test_initial_state_each_node_is_own_root(self):
        # --- ARRANGE ---
        size = 5

        # --- ACT ---
        uf = UnionFind(size)

        # --- ASSERT ---
        for i in range(size):
            self.assertEqual(uf.find(i), i, f"Node {i} must initially be its own root.")

    def test_union_with_zero_index_boundary(self):
        """
        REGRESSION TEST for: NameError: name 'root_a' is not defined.
        Guarantees that index 0 is not treated as a falsy condition in Python expressions.
        """
        # --- ARRANGE ---
        uf = UnionFind(size=5)
        item_zero = 0
        item_other = 3

        # --- ACT ---
        uf.union(item_other, item_zero)

        # --- ASSERT ---
        self.assertEqual(
            uf.find(item_zero),
            uf.find(item_other),
            "Index 0 and Index 3 must share the same canonical root after union."
        )
        self.assertEqual(uf.parent[item_zero], item_other)

    def test_union_with_zero_as_first_argument(self):
        """
        Guarantees that index 0 works symmetrically when passed as root_i.
        """
        # --- ARRANGE ---
        uf = UnionFind(size=5)
        item_zero = 0
        item_other = 4

        # --- ACT ---
        uf.union(item_zero, item_other)

        # --- ASSERT ---
        self.assertEqual(uf.find(item_zero), uf.find(item_other))
        self.assertEqual(uf.parent[item_other], item_zero)

    def test_transitive_clustering_chain(self):
        """
        Tests transitive clustering across a multi-node chain (0 -> 1 -> 2 -> 3).
        """
        # --- ARRANGE ---
        uf = UnionFind(size=6)

        # --- ACT ---
        uf.union(1, 0)
        uf.union(2, 1)
        uf.union(3, 2)

        # --- ASSERT ---
        root = uf.find(0)
        self.assertEqual(uf.find(1), root)
        self.assertEqual(uf.find(2), root)
        self.assertEqual(uf.find(3), root)
        # Disjoint nodes must remain unaffected
        self.assertEqual(uf.find(4), 4)
        self.assertEqual(uf.find(5), 5)

    def test_redundant_and_circular_unions(self):
        """
        Verifies that redundant unions do not create cycles or infinite recursion.
        """
        # --- ARRANGE ---
        uf = UnionFind(size=4)

        # --- ACT ---
        uf.union(1, 2)
        uf.union(2, 1)  # Redundant reverse call
        uf.union(1, 2)  # Duplicate call

        # --- ASSERT ---
        self.assertEqual(uf.find(1), uf.find(2))


class TestURLNormalization(unittest.TestCase):
    """
    Unit Tests for normalize_url and URL set extraction.
    """

    def test_strips_tracking_parameters(self):
        # --- ARRANGE ---
        raw_url = "https://example.com/article?utm_source=twitter&utm_medium=cpc&id=123&fbclid=xyz"

        # --- ACT ---
        normalized = normalize_url(raw_url)

        # --- ASSERT ---
        self.assertNotIn("utm_source", normalized)
        self.assertNotIn("utm_medium", normalized)
        self.assertNotIn("fbclid", normalized)
        self.assertIn("id=123", normalized)

    def test_converts_http_to_https_and_strips_www(self):
        # --- ARRANGE ---
        raw_url = "http://www.news-site.org/incident-report/"

        # --- ACT ---
        normalized = normalize_url(raw_url)

        # --- ASSERT ---
        self.assertTrue(normalized.startswith("https://news-site.org"))
        self.assertFalse(normalized.endswith("/"))

    def test_empty_or_none_url_handling(self):
        # --- ARRANGE / ACT / ASSERT ---
        self.assertEqual(normalize_url(""), "")
        self.assertEqual(normalize_url("   "), "")

    def test_get_normalized_url_set(self):
        # --- ARRANGE ---
        incident = {
            "source_urls": [
                "http://www.example.com/page/",
                "https://example.com/page?utm_campaign=daily",
                "https://another.com/news"
            ]
        }

        # --- ACT ---
        url_set = get_normalized_url_set(incident)

        # --- ASSERT ---
        # The first two URLs should collapse to the same normalized form
        self.assertEqual(len(url_set), 2)
        self.assertIn("https://example.com/page", url_set)
        self.assertIn("https://another.com/news", url_set)


class TestExactDuplicateDetection(unittest.TestCase):
    """
    Unit Tests for is_exact_duplicate.
    """

    def test_detects_exact_url_overlap(self):
        # --- ARRANGE ---
        inc1 = {
            "incident_id": "INC-001",
            "title": "OpenAI System Vulnerability Disclosed",
            "source_urls": ["http://www.techcrunch.com/2026/openai-vuln?utm_source=rss"]
        }
        inc2 = {
            "incident_id": "INC-002",
            "title": "Different Headline For Same Article",
            "source_urls": ["https://techcrunch.com/2026/openai-vuln"]
        }

        # --- ACT ---
        is_dup, reason = is_exact_duplicate(inc1, inc2)

        # --- ASSERT ---
        self.assertTrue(is_dup)
        self.assertIn("Exact URL match", reason)

    def test_detects_exact_normalized_title_match(self):
        # --- ARRANGE ---
        inc1 = {
            "incident_id": "INC-001",
            "title": "Deepfake Scam Targets European Banking Infrastructure",
            "source_urls": []
        }
        inc2 = {
            "incident_id": "INC-002",
            "title": "  DEEPFAKE SCAM TARGETS EUROPEAN BANKING INFRASTRUCTURE!  ",
            "source_urls": []
        }

        # --- ACT ---
        is_dup, reason = is_exact_duplicate(inc1, inc2)

        # --- ASSERT ---
        self.assertTrue(is_dup)
        self.assertIn("Exact normalized title match", reason)

    def test_rejects_dissimilar_incidents(self):
        # --- ARRANGE ---
        inc1 = {
            "title": "Tesla Autopilot Crash in Arizona",
            "source_urls": ["https://reuters.com/article-1"]
        }
        inc2 = {
            "title": "Algorithmic Hiring Bias Lawsuit Filed",
            "source_urls": ["https://bloomberg.com/article-2"]
        }

        # --- ACT ---
        is_dup, _ = is_exact_duplicate(inc1, inc2)

        # --- ASSERT ---
        self.assertFalse(is_dup)


class TestDuplicateMerging(unittest.TestCase):
    """
    Unit Tests for merge_duplicate_records.
    """

    def test_merges_all_fields_with_safety_rules(self):
        # --- ARRANGE ---
        inc1 = {
            "incident_id": "INC-20260901-001",
            "title": "Primary Title",
            "summary": "Short summary.",
            "full_text": "Short full text.",
            "financial_damage_usd": 150000,
            "source_urls": ["https://source1.com/story"],
            "affected_parties": ["OpenAI", "Users"]
        }
        inc2 = {
            "incident_id": "INC-20260901-002",
            "title": "Secondary Title",
            "summary": "This is a substantially longer and much more informative summary of the incident.",
            "full_text": "This is a much longer and comprehensive full text report containing forensic details.",
            "financial_damage_usd": 2500000,
            "source_urls": ["https://source2.com/story", "https://source1.com/story?ref=social"],
            "affected_parties": ["Hugging Face", "Users"]
        }

        # --- ACT ---
        merged = merge_duplicate_records(inc1, inc2)

        # --- ASSERT ---
        # 1. Primary ID is preserved
        self.assertEqual(merged["incident_id"], "INC-20260901-001")
        # 2. Longer summary and full_text chosen
        self.assertEqual(merged["summary"], inc2["summary"])
        self.assertEqual(merged["full_text"], inc2["full_text"])
        # 3. Maximum financial damage chosen
        self.assertEqual(merged["financial_damage_usd"], 2500000)
        # 4. URLs merged and deduplicated
        self.assertEqual(len(merged["source_urls"]), 2)
        # 5. Affected parties unioned
        self.assertEqual(set(merged["affected_parties"]), {"OpenAI", "Hugging Face", "Users"})


class TestTFIDFVectorization(unittest.TestCase):
    """
    Unit Tests for TF-IDF vectorization and candidate pre-filtering.
    """

    def test_tokenize_filters_stopwords_and_creates_bigrams(self):
        # --- ARRANGE ---
        text = "autonomous agents breaching safety protocols"

        # --- ACT ---
        tokens = tokenize(text)

        # --- ASSERT ---
        self.assertIn("autonomous", tokens)
        self.assertIn("breaching", tokens)
        self.assertIn("autonomous_breaching", tokens)

    def test_stopwords_only_corpus_does_not_raise_zerodivisionerror(self):
        """
        Verifies that a document consisting solely of generic stopwords does not crash TF-IDF normalization.
        """
        # --- ARRANGE ---
        corpus = ["the and for that with from this have were been"]

        # --- ACT ---
        vectors, vocab = compute_tfidf_vectors(corpus)

        # --- ASSERT ---
        self.assertEqual(len(vectors), 1)
        # Vector should be empty dictionary or have safe normalized values
        self.assertIsInstance(vectors[0], dict)

    def test_cosine_similarity_identical_and_orthogonal_vectors(self):
        # --- ARRANGE ---
        vec_a = {"ai": 0.6, "incident": 0.8}
        vec_b = {"ai": 0.6, "incident": 0.8}
        vec_c = {"aviation": 0.7071, "flight": 0.7071}

        # --- ACT ---
        sim_identical = cosine_similarity_vectors(vec_a, vec_b)
        sim_orthogonal = cosine_similarity_vectors(vec_a, vec_c)

        # --- ASSERT ---
        self.assertAlmostEqual(sim_identical, 1.0, places=3)
        self.assertEqual(sim_orthogonal, 0.0)

    def test_candidate_pairs_prefiltering(self):
        # --- ARRANGE ---
        incidents = [
            {
                "incident_id": "INC-1",
                "title": "Autonomous AI Agent Sandbox Escape on Hugging Face",
                "summary": "AI agents escaped containment and modified repository settings.",
                "affected_parties": ["OpenAI", "Hugging Face"],
                "source_urls": []
            },
            {
                "incident_id": "INC-2",
                "title": "Hugging Face Platform Attacked by Rogue AI Agents",
                "summary": "Containment breach allowed autonomous AI agents to execute unauthorized commands.",
                "affected_parties": ["OpenAI", "Hugging Face"],
                "source_urls": []
            },
            {
                "incident_id": "INC-3",
                "title": "Traffic Camera Facial Recognition False Arrest in Atlanta",
                "summary": "A misidentification by facial recognition software caused a wrongful arrest.",
                "affected_parties": ["Atlanta Police Department"],
                "source_urls": []
            }
        ]

        # --- ACT ---
        pairs, _ = compute_candidate_pairs_tfidf(incidents, min_similarity=0.20)

        # --- ASSERT ---
        pair_ids = [(p["id1"], p["id2"]) for p in pairs]
        # INC-1 and INC-2 must be detected as candidate pair
        self.assertTrue(
            ("INC-1", "INC-2") in pair_ids or ("INC-2", "INC-1") in pair_ids,
            "INC-1 and INC-2 must be identified as candidate duplicate pair."
        )
        # INC-3 must NOT be paired with INC-1 or INC-2
        self.assertFalse(
            any("INC-3" in p for p in pair_ids),
            "Unrelated INC-3 should not be paired with AI sandbox incidents."
        )


if __name__ == "__main__":
    unittest.main()
