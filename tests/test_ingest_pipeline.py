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
    Unit Tests for ArXiv harvester XML parsing, source_type tagging, and error resilience.
    """

    MOCK_ATOM_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2609.12345v1</id>
        <published>2026-09-11T14:30:00Z</published>
        <title> Jailbreak Attacks on Autonomous Frontier Models </title>
        <summary> Comprehensive empirical evaluation of prompt injection vectors. </summary>
      </entry>
    </feed>
    """

    @patch("urllib.request.urlopen")
    def test_fetch_arxiv_extracts_and_tags_correctly(self, mock_urlopen):
        # --- ARRANGE ---
        mock_resp = MagicMock()
        mock_resp.read.return_value = self.MOCK_ATOM_XML
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        # --- ACT ---
        results = fetch_arxiv(max_items=5)

        # --- ASSERT ---
        self.assertEqual(len(results), 1)
        item = results[0]
        self.assertEqual(item["source_type"], "arxiv")
        self.assertEqual(item["title"], "[ArXiv] Jailbreak Attacks on Autonomous Frontier Models")
        self.assertEqual(item["link"], "https://arxiv.org/abs/2609.12345v1")
        self.assertEqual(item["pub_date"], "2026-09-11")
        self.assertEqual(item["pub_date_clean"], "2026-09-11")
        self.assertIn("prompt injection", item["description"])

    @patch("scripts.ingest.safe_requests_get")
    @patch("urllib.request.urlopen", side_effect=Exception("Network timeout"))
    def test_fetch_arxiv_falls_back_to_recent_html_on_api_timeout(self, mock_urlopen, mock_safe_get):
        # --- ARRANGE ---
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = """
        <dl>
          <dt><a href="/abs/2609.99999" title="Abstract">arXiv:2609.99999</a></dt>
          <dd>
            <div class="list-title"><span class="descriptor">Title:</span>Novel Jailbreak Attacks on LLM Agents</div>
            <p class="mathjax">An empirical study showing critical prompt injection vulnerabilities in production.</p>
          </dd>
        </dl>
        """
        mock_safe_get.return_value = mock_resp

        # --- ACT ---
        results = fetch_arxiv(max_items=5)

        # --- ASSERT ---
        self.assertEqual(len(results), 1)
        item = results[0]
        self.assertEqual(item["source_type"], "arxiv")
        self.assertEqual(item["link"], "https://arxiv.org/abs/2609.99999")
        self.assertIn("Novel Jailbreak", item["title"])
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


if __name__ == "__main__":
    unittest.main()
