"""
Unit Tests for Ingestion Pipeline Core Deterministic Functions (scripts/ingest.py)
Following the strict Arrange - Act - Assert (AAA) pattern.
100% self-contained: 0 external network requests, 0 API tokens required.
"""

import unittest
from datetime import datetime, timedelta
import os
import json
from unittest.mock import patch, MagicMock

from scripts.ingest import (
    sanitize_incident_date,
    extract_key_entities,
    _load_harvest_keywords,
    fetch_arxiv,
    fetch_aiid_rss,
    fetch_google_news_multilane,
)


class TestDateSanitization(unittest.TestCase):
    """
    Unit Tests focusing on date boundary guardrails and invalid format resilience.
    """

    def test_valid_past_date_is_preserved(self):
        # --- ARRANGE ---
        valid_date = "2026-08-15"

        # --- ACT ---
        result = sanitize_incident_date(valid_date)

        # --- ASSERT ---
        self.assertEqual(result, "2026-08-15")

    def test_future_date_corrected_to_publication_date(self):
        """
        Guarantees that hallucinations with future dates are clamped to the publication date.
        """
        # --- ARRANGE ---
        future_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        pub_date = "2026-09-10"

        # --- ACT ---
        result = sanitize_incident_date(future_date, pub_date_clean=pub_date)

        # --- ASSERT ---
        self.assertEqual(result, pub_date)

    def test_future_date_corrected_to_today_when_no_pub_date(self):
        # --- ARRANGE ---
        future_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")

        # --- ACT ---
        result = sanitize_incident_date(future_date, pub_date_clean="")

        # --- ASSERT ---
        self.assertEqual(result, today)

    def test_corrupted_or_non_iso_date_returns_fallback(self):
        # --- ARRANGE ---
        corrupt_inputs = [
            "N/A",
            "yesterday",
            "2026/08/15",
            "invalid-date-string",
            "",
            None
        ]
        pub_date = "2026-09-01"

        # --- ACT & ASSERT ---
        for raw in corrupt_inputs:
            with self.subTest(raw=raw):
                res = sanitize_incident_date(raw, pub_date_clean=pub_date)
                self.assertEqual(res, pub_date)


class TestHarvestKeywordsConfiguration(unittest.TestCase):
    """
    Unit Tests for config/harvest_keywords.json integrity and loader resilience.
    """

    def test_harvest_keywords_json_has_all_required_sections(self):
        # --- ARRANGE & ACT ---
        keywords = _load_harvest_keywords()

        # --- ASSERT ---
        self.assertIn("rss", keywords)
        self.assertIn("gdelt", keywords)
        self.assertIn("subjects", keywords["rss"])
        self.assertIn("incidents", keywords["rss"])
        self.assertIn("url_entities", keywords["gdelt"])
        self.assertIn("organizations", keywords["gdelt"])
        self.assertIn("incident_keywords", keywords["gdelt"])
        self.assertIn("exclude_url_terms", keywords["gdelt"])

        self.assertIn("arxiv", keywords)
        self.assertIn("categories", keywords["arxiv"])
        self.assertIn("keywords", keywords["arxiv"])

    def test_keywords_contain_no_empty_strings(self):
        # --- ARRANGE ---
        keywords = _load_harvest_keywords()

        # --- ACT & ASSERT ---
        for section, sub in [
            ("rss", "subjects"),
            ("rss", "incidents"),
            ("gdelt", "url_entities"),
            ("gdelt", "organizations"),
            ("gdelt", "incident_keywords"),
            ("arxiv", "categories"),
            ("arxiv", "keywords")
        ]:
            items = keywords[section][sub]
            self.assertGreater(len(items), 0, f"{section}.{sub} must not be empty.")
            for item in items:
                self.assertTrue(bool(item.strip()), f"Empty item found in {section}.{sub}")


class TestKeyEntityExtraction(unittest.TestCase):
    """
    Unit Tests for extract_key_entities.
    """

    def test_extracts_significant_words_ignoring_stopwords(self):
        # --- ARRANGE ---
        text = "The Anthropic and OpenAI models were used for unauthorized intrusion"

        # --- ACT ---
        entities = extract_key_entities(text)

        # --- ASSERT ---
        self.assertIn("anthropic", entities)
        self.assertIn("openai", entities)
        self.assertIn("unauthorized", entities)
        self.assertIn("intrusion", entities)
        # Stopwords must be filtered out
        self.assertNotIn("the", entities)
        self.assertNotIn("and", entities)
        self.assertNotIn("were", entities)
        self.assertNotIn("for", entities)

    def test_handles_empty_or_none_safely(self):
        # --- ARRANGE / ACT / ASSERT ---
        self.assertEqual(extract_key_entities(""), set())
        self.assertEqual(extract_key_entities(None), set())


class TestArXivHarvester(unittest.TestCase):
    """
    Unit Tests for ArXiv multi-category recent harvester HTML parsing, tagging, and resilience.
    """

    MOCK_RECENT_HTML = """
    <dl>
      <dt><a href="/abs/2609.12345" title="Abstract">arXiv:2609.12345</a></dt>
      <dd>
        <div class="list-title"><span class="descriptor">Title:</span>Jailbreak Attacks on LLM Autonomous Frontier Models</div>
        <div class="list-subjects"><span class="primary-subject">Cryptography and Security (cs.CR)</span></div>
        <p class="mathjax">Comprehensive empirical evaluation of prompt injection vectors.</p>
      </dd>
    </dl>
    """

    @patch("scripts.ingest.safe_requests_get")
    def test_fetch_arxiv_extracts_and_tags_correctly(self, mock_safe_get):
        # --- ARRANGE ---
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self.MOCK_RECENT_HTML
        mock_safe_get.return_value = mock_resp

        # --- ACT ---
        results = fetch_arxiv(max_items=5)

        # --- ASSERT ---
        self.assertGreaterEqual(len(results), 1)
        item = results[0]
        self.assertEqual(item["source_type"], "arxiv")
        self.assertIn("Jailbreak Attacks", item["title"])
        self.assertEqual(item["link"], "https://arxiv.org/abs/2609.12345")
        self.assertEqual(item["pub_date_clean"], datetime.now().strftime("%Y-%m-%d"))
        self.assertIn("prompt injection", item["description"])

    @patch("scripts.ingest.safe_requests_get", return_value=None)
    @patch("urllib.request.urlopen", side_effect=Exception("Network timeout"))
    def test_fetch_arxiv_handles_total_network_failure_cleanly(self, mock_urlopen, mock_safe_get):
        # --- ARRANGE / ACT ---
        results = fetch_arxiv(max_items=5)

        # --- ASSERT ---
        self.assertEqual(results, [])


class TestAIIDHarvester(unittest.TestCase):
    """
    Unit Tests for AI Incident Database (AIID) RSS parsing, tagging, and error resilience.
    """

    MOCK_RSS_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>AI Incident Database</title>
        <item>
          <title>Autonomous Delivery Robot Collides With Pedestrian</title>
          <link>https://example.com/news/delivery-robot-accident</link>
          <pubDate>Thu, 10 Sep 2026 00:00:00 GMT</pubDate>
          <description>&lt;p&gt;A self-driving delivery unit failed to yield at crosswalk.&lt;/p&gt;</description>
        </item>
      </channel>
    </rss>
    """

    @patch("urllib.request.urlopen")
    def test_fetch_aiid_rss_extracts_and_tags_correctly(self, mock_urlopen):
        # --- ARRANGE ---
        mock_resp = MagicMock()
        mock_resp.read.return_value = self.MOCK_RSS_XML
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        # --- ACT ---
        results = fetch_aiid_rss(max_items=5)

        # --- ASSERT ---
        self.assertEqual(len(results), 1)
        item = results[0]
        self.assertEqual(item["source_type"], "aiid")
        self.assertEqual(item["title"], "Autonomous Delivery Robot Collides With Pedestrian")
        self.assertEqual(item["link"], "https://example.com/news/delivery-robot-accident")
        self.assertEqual(item["pub_date_clean"], "2026-09-10")
        self.assertIn("self-driving delivery unit", item["description"])
        self.assertNotIn("<p>", item["description"])

    @patch("urllib.request.urlopen", side_effect=Exception("Connection refused"))
    def test_fetch_aiid_rss_handles_network_failure_cleanly(self, mock_urlopen):
        # --- ARRANGE / ACT ---
        results = fetch_aiid_rss(max_items=5)

        # --- ASSERT ---
        self.assertEqual(results, [])


class TestMultiLaneHarvester(unittest.TestCase):
    """
    Unit Tests for Multi-Lane Topic-Partitioned Harvester and Lane Keyword Completeness.
    """

    def test_all_subjects_and_incidents_covered_in_lanes(self):
        kw = _load_harvest_keywords()
        all_subjects = set(kw.get("rss", {}).get("subjects", []))
        all_incidents = set(kw.get("rss", {}).get("incidents", []))
        lanes = kw.get("rss", {}).get("lanes", {})

        self.assertGreaterEqual(len(lanes), 5, "Must have at least 5 structured topic lanes.")

        covered_subjects = set()
        covered_incidents = set()
        for lane_cfg in lanes.values():
            covered_subjects.update(lane_cfg.get("subjects", []))
            covered_incidents.update(lane_cfg.get("incidents", []))

        # 100% Keyword Retention Check
        missing_subjects = all_subjects - covered_subjects
        missing_incidents = all_incidents - covered_incidents
        self.assertEqual(missing_subjects, set(), f"Missing subjects from lanes: {missing_subjects}")
        self.assertEqual(missing_incidents, set(), f"Missing incident terms from lanes: {missing_incidents}")

    @patch("scripts.ingest.fetch_google_news")
    def test_fetch_google_news_multilane_aggregates_and_deduplicates(self, mock_fetch_gnews):
        # Mock sub-query responses with duplicate URLs
        mock_fetch_gnews.return_value = [
            {"title": "OpenAI Agent Data Leak", "link": "https://example.com/openai-leak", "pub_date_clean": "2026-09-25"},
            {"title": "Anthropic Prompt Injection", "link": "https://example.com/anthropic-pi", "pub_date_clean": "2026-09-25"}
        ]

        results = fetch_google_news_multilane(max_per_lane=2, max_total_items=10)

        self.assertGreaterEqual(len(results), 2)
        urls = [r["link"] for r in results]
        self.assertEqual(len(urls), len(set(urls)), "Multilane results must be strictly deduplicated by URL.")


if __name__ == "__main__":
    unittest.main()
