"""
Integration Tests for Supabase Synchronization (scripts/migrate_json_to_supabase.py)
Following the strict Arrange - Act - Assert (AAA) pattern with mocked HTTP calls.
100% self-contained: 0 external network requests, 0 API tokens required.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import io

from scripts.migrate_json_to_supabase import (
    sync_supabase_records,
    post_to_supabase_table,
)


class TestSupabaseRecordSync(unittest.TestCase):
    """
    Integration Tests for Supabase sync operations using the AAA pattern.
    """

    @patch("scripts.migrate_json_to_supabase.post_to_supabase_table")
    @patch("urllib.request.urlopen")
    def test_sync_skips_cleanly_on_empty_records(self, mock_urlopen, mock_post):
        """
        Ensures sync_supabase_records returns False and avoids HTTP endpoints
        when provided with an empty record list.
        """
        # --- ARRANGE ---
        url = "https://mock-supabase.co"
        secret_key = "sb_secret_mock_test_key"
        table_name = "edges"
        empty_records = []
        primary_key = "edge_id"

        # --- ACT ---
        result = sync_supabase_records(url, secret_key, table_name, empty_records, primary_key)

        # --- ASSERT ---
        self.assertFalse(result, "Sync must return False for empty record payloads.")
        mock_post.assert_not_called()
        mock_urlopen.assert_not_called()

    @patch("scripts.migrate_json_to_supabase.post_to_supabase_table")
    def test_sync_aborts_without_valid_credentials(self, mock_post):
        """
        Ensures missing credentials halt the sync process immediately.
        """
        # --- ARRANGE ---
        empty_url = ""
        empty_key = ""
        records = [{"incident_id": "INC-20260913-001"}]

        # --- ACT ---
        result = sync_supabase_records(empty_url, empty_key, "incidents", records, "incident_id")

        # --- ASSERT ---
        self.assertFalse(result, "Sync must halt immediately when credentials are empty.")
        mock_post.assert_not_called()

    @patch("urllib.request.urlopen")
    def test_post_to_supabase_table_success(self, mock_urlopen):
        """
        Tests successful POST payload submission to Supabase REST API endpoint.
        """
        # --- ARRANGE ---
        url = "https://mock-supabase.co"
        key = "sb_secret_valid_key_123"
        records = [{"edge_id": "EDGE-001", "source_id": "INC-1", "target_id": "INC-2"}]

        mock_resp = MagicMock()
        mock_resp.status = 201
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        # --- ACT ---
        success = post_to_supabase_table(url, key, "edges", records, "edge_id")

        # --- ASSERT ---
        self.assertTrue(success)
        mock_urlopen.assert_called_once()
        called_req = mock_urlopen.call_args[0][0]
        self.assertEqual(called_req.get_full_url(), "https://mock-supabase.co/rest/v1/edges")
        self.assertEqual(called_req.get_header("Apikey"), key)
        self.assertEqual(called_req.get_header("Authorization"), f"Bearer {key}")


if __name__ == "__main__":
    unittest.main()
