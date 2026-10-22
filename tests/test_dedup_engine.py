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
    stem_word,
    compute_entity_and_temporal_boost,
    compute_tfidf_vectors,
    cosine_similarity_vectors,
    compute_candidate_pairs_tfidf,
    consolidate_new_against_existing,
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

    def test_merges_duplicate_records_initializes_anchor_milestone(self):
        # --- ARRANGE ---
        inc1 = {
            "incident_id": "INC-20261001-001",
            "title": "Initial Outage Reported at Cloud Provider",
            "summary": "Cloud provider experienced a multi-region outage. Service was disrupted.",
            "date": "2026-10-01",
            "source_urls": ["https://tech.example.com/outage-day1"]
        }
        inc2 = {
            "incident_id": "INC-20261005-002",
            "title": "Cloud Provider Outage Root Cause Revealed as Agent Deadlock",
            "summary": "Post-mortem analysis shows an autonomous scheduler agent entered an infinite deadlock loop.",
            "date": "2026-10-05",
            "source_urls": ["https://forensics.example.com/post-mortem"]
        }

        # --- ACT ---
        merged = merge_duplicate_records(inc1, inc2)

        # --- ASSERT ---
        self.assertIn("timeline", merged)
        self.assertEqual(len(merged["timeline"]), 2)
        
        # Milestone 1: Anchor
        m1 = merged["timeline"][0]
        self.assertEqual(m1["date"], "2026-10-01")
        self.assertEqual(m1["phase"], "initial_report")
        self.assertEqual(m1["source_url"], "https://tech.example.com/outage-day1")

        # Milestone 2: Evolving follow up
        m2 = merged["timeline"][1]
        self.assertEqual(m2["date"], "2026-10-05")
        self.assertEqual(m2["phase"], "follow_up")
        self.assertEqual(m2["source_url"], "https://forensics.example.com/post-mortem")
        self.assertEqual(merged["last_updated_date"], "2026-10-05")
        self.assertEqual(merged["date"], "2026-10-01")

    def test_merges_duplicate_records_with_llm_milestone_info(self):
        # --- ARRANGE ---
        inc1 = {
            "incident_id": "INC-20260915-001",
            "title": "AI Image Generator Generated Defamatory Content",
            "summary": "A public lawsuit was initiated against an image generation model.",
            "date": "2026-09-15",
            "source_urls": ["https://news.example.com/lawsuit-filed"]
        }
        inc2 = {
            "incident_id": "INC-20261010-003",
            "title": "Court Approves $5M Settlement in AI Defamation Case",
            "summary": "The parties reached a 5 million dollar settlement approved by the federal judge.",
            "date": "2026-10-10",
            "financial_damage_usd": 5000000,
            "source_urls": ["https://legal.example.com/settlement-approved"]
        }
        milestone_info = {
            "evolution_type": "new_milestone",
            "milestone_phase": "legal_settlement",
            "summary_delta": "Federal court approves $5,000,000 settlement resolving the litigation."
        }

        # --- ACT ---
        merged = merge_duplicate_records(inc1, inc2, milestone_info=milestone_info)

        # --- ASSERT ---
        self.assertEqual(len(merged["timeline"]), 2)
        settlement_milestone = merged["timeline"][1]
        self.assertEqual(settlement_milestone["phase"], "legal_settlement")
        self.assertEqual(settlement_milestone["summary_delta"], "Federal court approves $5,000,000 settlement resolving the litigation.")
        self.assertEqual(merged["financial_damage_usd"], 5000000)
        self.assertEqual(merged["last_updated_date"], "2026-10-10")

    def test_milestone_chronological_ordering_and_earliest_date(self):
        # --- ARRANGE: inc2 is earlier than inc1 ---
        inc1 = {
            "incident_id": "INC-20261012-001",
            "title": "Government Sanctions Firm over Deepfake Disinformation",
            "summary": "Sanctions imposed after investigation.",
            "date": "2026-10-12",
            "source_urls": ["https://gov.example.com/sanctions"]
        }
        inc2 = {
            "incident_id": "INC-20261002-001",
            "title": "First Reports of Deepfake Campaign Targeting Election",
            "summary": "Initial sightings of automated bots spreading synthetic media.",
            "date": "2026-10-02",
            "source_urls": ["https://watchdog.example.com/initial-findings"]
        }

        # --- ACT ---
        merged = merge_duplicate_records(inc1, inc2)

        # --- ASSERT ---
        # First-Reported-Date Principle
        self.assertEqual(merged["date"], "2026-10-02")
        self.assertEqual(len(merged["timeline"]), 2)
        self.assertEqual(merged["timeline"][0]["date"], "2026-10-02")
        self.assertEqual(merged["timeline"][0]["phase"], "initial_report")
        self.assertEqual(merged["timeline"][1]["date"], "2026-10-12")
        self.assertEqual(merged["last_updated_date"], "2026-10-12")


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

    def test_morphological_stemming_matches_replication_and_replicate(self):
        # --- ARRANGE ---
        text_a = "anthropic warning on self replication risks"
        text_b = "anthropic warns models may self replicate"

        # --- ACT ---
        tokens_a = set(tokenize(text_a))
        tokens_b = set(tokenize(text_b))
        shared_stems = {t for t in (tokens_a & tokens_b) if t.startswith("st_")}

        # --- ASSERT ---
        self.assertIn("st_replic", shared_stems)
        self.assertIn("st_warn", shared_stems)

    def test_subtoken_entity_matching_catches_name_variants(self):
        # --- ARRANGE ---
        inc_a = {
            "title": "Death of patient following clinical priority misclassification by Core-MG",
            "summary": "A psychologist died waiting for an ICU bed.",
            "date": "2026-10-19",
            "affected_parties": ["Rebeca Molina", "Family of Rebeca Molina"],
            "geographic_scope": ["Brazil"]
        }
        inc_b = {
            "title": "PJF Files Public Civil Action Over New State Health Bed Regulation System Failures",
            "summary": "Lawsuit filed over Core/MG delays.",
            "date": "2026-10-19",
            "affected_parties": ["Prefeitura de Juiz de Fora (PJF)", "Rebeca Cardoso Tenente Molina"],
            "geographic_scope": ["Brazil"]
        }

        # --- ACT ---
        boost, shared_entities = compute_entity_and_temporal_boost(inc_a, inc_b)

        # --- ASSERT ---
        self.assertIn("rebeca", shared_entities)
        self.assertIn("molina", shared_entities)
        self.assertGreaterEqual(boost, 0.20)

    def test_temporal_vendor_boost_within_7_days_vs_distant(self):
        # --- ARRANGE ---
        inc_day1 = {
            "title": "Anthropic Warning on Self-Replication",
            "summary": "Report released.",
            "date": "2026-10-13",
            "affected_parties": ["Anthropic"],
            "geographic_scope": ["United States"]
        }
        inc_day2 = {
            "title": "Anthropic Warns Models May Self-Replicate",
            "summary": "Follow-up coverage.",
            "date": "2026-10-14",
            "affected_parties": ["Anthropic"],
            "geographic_scope": ["United States"]
        }
        inc_distant = {
            "title": "Anthropic API Outage in Europe",
            "summary": "Unrelated outage months earlier.",
            "date": "2026-06-01",
            "affected_parties": ["Anthropic"],
            "geographic_scope": ["United States"]
        }

        # --- ACT ---
        boost_close, _ = compute_entity_and_temporal_boost(inc_day1, inc_day2)
        boost_distant, _ = compute_entity_and_temporal_boost(inc_day1, inc_distant)

        # --- ASSERT ---
        self.assertAlmostEqual(boost_close, 0.08, places=2)
        self.assertEqual(boost_distant, 0.0)


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


class TestIncrementalConsolidation(unittest.TestCase):
    """
    Unit Tests for O(K) incremental deduplication & merging against canonical catalog.
    """

    def test_merges_exact_url_overlap_into_existing(self):
        existing = [
            {
                "incident_id": "INC-20260924-001",
                "title": "OpenAI AI Agent Unauthorised Access to Australian Government",
                "date": "2026-09-24",
                "summary": "AI Agent compromised Medicare Portal.",
                "affected_parties": ["OpenAI", "Australian Government"],
                "source_urls": ["https://www.abc.net.au/news/2026-09-24/openai-breach"],
                "severity": "high",
                "verification_status": "confirmed"
            }
        ]
        new_incidents = [
            {
                "incident_id": "INC-20260925-999",
                "title": "Medicare Portal Infiltration via OpenAI Agent",
                "date": "2026-09-25",
                "summary": "New report on the Medicare breach.",
                "affected_parties": ["OpenAI", "Medicare"],
                "source_urls": [
                    "https://www.abc.net.au/news/2026-09-24/openai-breach?ref=twitter",
                    "https://www.smh.com.au/technology/australia-medicare-breach"
                ],
                "severity": "critical",
                "verification_status": "confirmed"
            }
        ]

        result = consolidate_new_against_existing(new_incidents, existing, api_key="")

        self.assertEqual(len(result), 1, "Should retain exactly 1 canonical incident.")
        canonical = result[0]
        self.assertEqual(canonical["incident_id"], "INC-20260924-001")
        self.assertEqual(canonical["date"], "2026-09-24", "Canonical date must remain the first reported date.")
        self.assertEqual(len(canonical["source_urls"]), 2, "Should merge new source URL.")
        self.assertIn("https://www.smh.com.au/technology/australia-medicare-breach", canonical["source_urls"])

    def test_appends_distinct_incident(self):
        existing = [
            {
                "incident_id": "INC-20260924-001",
                "title": "OpenAI AI Agent Unauthorised Access",
                "date": "2026-09-24",
                "summary": "AI Agent compromised Medicare Portal.",
                "affected_parties": ["OpenAI"],
                "source_urls": ["https://www.abc.net.au/news/2026-09-24/openai-breach"]
            }
        ]
        new_incidents = [
            {
                "incident_id": "INC-20260925-002",
                "title": "Autonomous Drone Navigation Failure in Berlin",
                "date": "2026-09-25",
                "summary": "Delivery drone crash landed due to GPS spoofing.",
                "affected_parties": ["DHL"],
                "source_urls": ["https://www.spiegel.de/drone-crash-berlin"]
            }
        ]

        result = consolidate_new_against_existing(new_incidents, existing, api_key="")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["incident_id"], "INC-20260924-001")
        self.assertEqual(result[1]["incident_id"], "INC-20260925-002")


if __name__ == "__main__":
    unittest.main()
