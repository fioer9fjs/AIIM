"""
Integration Tests for Supabase Synchronization (scripts/migrate_json_to_supabase.py)
Following the strict Arrange - Act - Assert (AAA) pattern with mocked HTTP calls.
100% self-contained: 0 external network requests, 0 API tokens required.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import json
import io

from scripts.migrate_json_to_supabase import (
    sync_supabase_records,
    post_to_supabase_table,
    get_supabase_credentials,
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

    @patch("scripts.migrate_json_to_supabase.load_env_file")
    def test_get_supabase_credentials_rejects_legacy_jwt_anon_key(self, _):
        """
        ARCHITECTURAL INVARIANT 2 & RULE 3:
        Rejects legacy JWT format keys (e.g., 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...')
        and mandates modern 'sb_secret_' tokens.
        """
        # --- ARRANGE ---
        env_dict = {
            "SUPABASE_URL": "https://xyz.supabase.co",
            "SUPABASE_SECRET_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.legacy_token_sample"
        }

        with patch.dict(os.environ, env_dict, clear=True):
            # --- ACT ---
            url, key = get_supabase_credentials()

            # --- ASSERT ---
            self.assertEqual(url, "https://xyz.supabase.co")
            self.assertEqual(key, "", "Legacy JWT keys must be rejected and return an empty key.")

    @patch("scripts.migrate_json_to_supabase.load_env_file")
    def test_get_supabase_credentials_accepts_valid_modern_key(self, _):
        """
        Accepts modern sb_secret_ service credentials.
        """
        # --- ARRANGE ---
        env_dict = {
            "SUPABASE_URL": "https://xyz.supabase.co",
            "SUPABASE_SECRET_KEY": "sb_secret_prod_valid_token_789"
        }

        with patch.dict(os.environ, env_dict, clear=True):
            # --- ACT ---
            url, key = get_supabase_credentials()

            # --- ASSERT ---
            self.assertEqual(url, "https://xyz.supabase.co")
            self.assertEqual(key, "sb_secret_prod_valid_token_789")


if __name__ == "__main__":
    unittest.main()
