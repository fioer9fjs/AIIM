"""
Unit Tests for Adaptive Dynamic Keyword Evolution (scripts/dynamic_keywords.py)
Following the strict Arrange - Act - Assert (AAA) pattern.
100% self-contained: 0 external network requests, 0 API tokens required.
"""

import unittest
from datetime import datetime, timedelta
import os
import json
from unittest.mock import patch, MagicMock

from scripts.dynamic_keywords import (
    clean_candidate_phrase,
    anti_drift_validate_term,
    map_incident_to_lane,
    extract_emerging_entities_from_incident,
    apply_keyword_decay_and_cleanup,
    learn_and_update_keywords,
    get_top_dynamic_keywords_for_lane,
    load_dynamic_keywords,
    save_dynamic_keywords,
)


class TestAntiDriftValidator(unittest.TestCase):
    """
    Unit tests for anti-drift guardrail and stopword/financial term filtering.
    """

    def test_valid_emerging_terms_pass(self):
        # --- ARRANGE ---
        valid_terms = [
            "Claude Code",
            "Flock Safety",
            "sandbox escape",
            "voice clone extortion",
            "API credential",
            "unlisted upload",
            "prompt injection",
            "Waymo collision",
            "facial recognition"
        ]

        # --- ACT & ASSERT ---
        for term in valid_terms:
            with self.subTest(term=term):
                self.assertTrue(anti_drift_validate_term(term), f"Term '{term}' should be valid.")

    def test_stopwords_and_financial_noise_are_rejected(self):
        # --- ARRANGE ---
        rejected_terms = [
            "the",
            "and",
            "about",
            "for that with",
            "revenue",
            "stock shares",
            "quarterly profit",
            "chief executive officer",
            "investors conference",
            "announced today",
            "12345",
            "2026",
            "ai",
            "",
            None
        ]

        # --- ACT & ASSERT ---
        for term in rejected_terms:
            with self.subTest(term=term):
                self.assertFalse(anti_drift_validate_term(term), f"Term '{term}' should be rejected.")

    def test_too_long_or_too_many_words_rejected(self):
        # --- ARRANGE ---
        long_terms = [
            "a" * 40,
            "this is a four word phrase",
            "super long phrase with multiple words describing an incident"
        ]

        # --- ACT & ASSERT ---
        for term in long_terms:
            with self.subTest(term=term):
                self.assertFalse(anti_drift_validate_term(term))

    def test_clean_candidate_phrase_strips_leading_and_trailing_stopwords(self):
        # --- ARRANGE ---
        test_cases = [
            ("and API credential", "API credential"),
            ("the sandbox escape for", "sandbox escape"),
            ("  Claude 3.5 Sonnet  ", "Claude 35 Sonnet"),
            ("with prompt injection", "prompt injection")
        ]

        # --- ACT & ASSERT ---
        for raw, expected in test_cases:
            with self.subTest(raw=raw):
                cleaned = clean_candidate_phrase(raw)
                self.assertEqual(cleaned, expected)


class TestLaneMapping(unittest.TestCase):
    """
    Unit tests for map_incident_to_lane classification routing.
    """

    def test_routes_autonomous_agent(self):
        # --- ARRANGE ---
        inc = {
            "system_classification": "autonomous_agent",
            "title": "AI Agent leaked credentials",
            "summary": "Autonomous crawler scraped private repos."
        }

        # --- ACT ---
        lane = map_incident_to_lane(inc)

        # --- ASSERT ---
        self.assertEqual(lane, "autonomous_agents_cyber")

    def test_routes_biometrics(self):
        # --- ARRANGE ---
        inc = {
            "system_classification": "biometric_identification",
            "title": "Flock Safety camera error",
            "summary": "Facial recognition false arrest."
        }

        # --- ACT ---
        lane = map_incident_to_lane(inc)

        # --- ASSERT ---
        self.assertEqual(lane, "biometrics_police_surveillance")

    def test_routes_mobility(self):
        # --- ARRANGE ---
        inc = {
            "primary_purpose": "autonomous_mobility",
            "title": "Waymo vehicle crash",
            "summary": "Self-driving car stopped abruptly."
        }

        # --- ACT ---
        lane = map_incident_to_lane(inc)

        # --- ASSERT ---
        self.assertEqual(lane, "autonomous_mobility_robotics")

    def test_routes_deepfakes(self):
        # --- ARRANGE ---
        inc = {
            "harm_type": "copyright_ip",
            "title": "Deepfake voice clone scam",
            "summary": "Executive audio clone used in wire fraud."
        }

        # --- ACT ---
        lane = map_incident_to_lane(inc)

        # --- ASSERT ---
        self.assertEqual(lane, "multimodal_media_deepfakes")

    def test_routes_social_harm(self):
        # --- ARRANGE ---
        inc = {
            "harm_type": "psychological_harm",
            "title": "Chatbot emotional harm",
            "summary": "Character AI companion led to psychological distress."
        }

        # --- ACT ---
        lane = map_incident_to_lane(inc)

        # --- ASSERT ---
        self.assertEqual(lane, "social_chatbots_harm_governance")


class TestEmergingEntityExtraction(unittest.TestCase):
    """
    Unit tests for extract_emerging_entities_from_incident.
    """

    def test_extracts_affected_parties_and_technical_subtypes(self):
        # --- ARRANGE ---
        incident = {
            "title": "OpenAI Agent Sandbox Escape",
            "summary": "Agent escaped execution environment and leaked credentials.",
            "system_classification": "autonomous_agent",
            "affected_parties": ["UNM Digital Library", "OpenAI"],
            "failure_mode": "Unauthorized sandbox escape allowed reading server logs",
            "root_cause_subtype": "API credential exposure"
        }

        # --- ACT ---
        candidates = extract_emerging_entities_from_incident(incident)

        # --- ASSERT ---
        terms = [c["term"] for c in candidates]
        self.assertIn("UNM Digital Library", terms)
        self.assertIn("OpenAI", terms)
        self.assertTrue(any("sandbox escape" in t.lower() for t in terms))
        self.assertTrue(any("credential" in t.lower() for t in terms))
        for c in candidates:
            self.assertEqual(c["lane"], "autonomous_agents_cyber")


class TestDecayAndCleanup(unittest.TestCase):
    """
    Unit tests for apply_keyword_decay_and_cleanup.
    """

    def test_decay_applies_to_old_terms_and_purges_below_threshold(self):
        # --- ARRANGE ---
        today = datetime.now()
        ten_days_ago = (today - timedelta(days=10)).strftime("%Y-%m-%d")
        thirty_days_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")

        mock_pool = {
            "_meta": {
                "decay_rate_daily": 0.05,
                "min_weight_threshold": 0.20,
                "max_ttl_days": 21,
                "max_active_per_lane": 4
            },
            "lanes": {
                "frontier_llms_leaks": [
                    {
                        "term": "Active Model",
                        "type": "subject",
                        "weight": 1.0,
                        "hit_count": 5,
                        "last_hit": today_str
                    },
                    {
                        "term": "Ten Day Inactive",
                        "type": "incident",
                        "weight": 0.50,
                        "hit_count": 1,
                        "last_hit": ten_days_ago
                    },
                    {
                        "term": "Expired TTL Term",
                        "type": "subject",
                        "weight": 0.90,
                        "hit_count": 2,
                        "last_hit": thirty_days_ago
                    },
                    {
                        "term": "Low Weight Decayed Term",
                        "type": "incident",
                        "weight": 0.21,
                        "hit_count": 1,
                        "last_hit": ten_days_ago
                    }
                ]
            }
        }

        # --- ACT ---
        decayed_cnt, purged_cnt = apply_keyword_decay_and_cleanup(mock_pool)

        # --- ASSERT ---
        surviving = mock_pool["lanes"]["frontier_llms_leaks"]
        surviving_terms = [t["term"] for t in surviving]
        
        # Active Model should survive with untouched weight
        self.assertIn("Active Model", surviving_terms)
        active_entry = next(t for t in surviving if t["term"] == "Active Model")
        self.assertEqual(active_entry["weight"], 1.0)

        # Ten Day Inactive should decay: 0.50 * (0.95^10) ~ 0.299 >= 0.20 -> survives
        self.assertIn("Ten Day Inactive", surviving_terms)
        ten_day_entry = next(t for t in surviving if t["term"] == "Ten Day Inactive")
        self.assertAlmostEqual(ten_day_entry["weight"], round(0.50 * ((0.95)**10), 3), places=2)

        # Expired TTL Term (>21 days) must be purged
        self.assertNotIn("Expired TTL Term", surviving_terms)

        # Low Weight Decayed Term: 0.21 * (0.95^10) ~ 0.125 < 0.20 -> must be purged
        self.assertNotIn("Low Weight Decayed Term", surviving_terms)

        self.assertGreaterEqual(purged_cnt, 2)


class TestLearningLoop(unittest.TestCase):
    """
    Unit tests for learn_and_update_keywords and get_top_dynamic_keywords_for_lane.
    """

    @patch("scripts.dynamic_keywords.load_dynamic_keywords")
    @patch("scripts.dynamic_keywords.save_dynamic_keywords")
    def test_learn_and_update_reinforces_and_adds_novel(self, mock_save, mock_load):
        # --- ARRANGE ---
        mock_pool = {
            "_meta": {
                "decay_rate_daily": 0.05,
                "min_weight_threshold": 0.20,
                "max_ttl_days": 21,
                "max_active_per_lane": 4
            },
            "lanes": {
                "frontier_llms_leaks": [
                    {
                        "term": "Claude Code",
                        "type": "subject",
                        "weight": 0.80,
                        "hit_count": 2,
                        "last_hit": "2026-09-20"
                    }
                ]
            }
        }
        mock_load.return_value = mock_pool

        new_incidents = [
            {
                "title": "Claude Code Prompt Leak",
                "summary": "Claude Code exposed internal instructions.",
                "system_classification": "general_purpose_model",
                "affected_parties": ["Claude Code"],
                "failure_mode": "Novel Prompt Extraction Attack",
                "root_cause_subtype": "Jailbreak bypass"
            }
        ]

        # --- ACT ---
        telemetry = learn_and_update_keywords(new_incidents)

        # --- ASSERT ---
        self.assertGreaterEqual(telemetry["reinforced"], 1)
        # Check that Claude Code weight was reinforced
        claude_entry = next(t for t in mock_pool["lanes"]["frontier_llms_leaks"] if t["term"].lower() == "claude code")
        self.assertEqual(claude_entry["hit_count"], 3)
        self.assertGreaterEqual(claude_entry["weight"], 0.95)
        self.assertEqual(claude_entry["last_hit"], datetime.now().strftime("%Y-%m-%d"))

        # Check that save was called
        mock_save.assert_called_once()


if __name__ == "__main__":
    unittest.main()
