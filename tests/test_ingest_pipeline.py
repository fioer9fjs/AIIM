"""
Unit Tests for Ingestion Pipeline Core Deterministic Functions (scripts/ingest.py)
Following the strict Arrange - Act - Assert (AAA) pattern.
100% self-contained: 0 external network requests, 0 API tokens required.
"""

import unittest
from datetime import datetime, timedelta
import os
import json

from scripts.ingest import (
    sanitize_incident_date,
    extract_key_entities,
    _load_harvest_keywords,
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

    def test_keywords_contain_no_empty_strings(self):
        # --- ARRANGE ---
        keywords = _load_harvest_keywords()

        # --- ACT & ASSERT ---
        for section, sub in [
            ("rss", "subjects"),
            ("rss", "incidents"),
            ("gdelt", "url_entities"),
            ("gdelt", "organizations"),
            ("gdelt", "incident_keywords")
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


if __name__ == "__main__":
    unittest.main()
