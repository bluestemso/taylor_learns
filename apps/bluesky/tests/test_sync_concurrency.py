from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.bluesky.models import BlueskySourceSettings
from apps.bluesky.sync import run_sync


class TestSyncConcurrency(TestCase):
    def setUp(self):
        self.source_settings = BlueskySourceSettings.objects.create(
            handle="taylorlearns.com",
            did="did:plc:abc123",
            profile_url="https://bsky.app/profile/taylorlearns.com",
            backfill_start_date=date(2024, 1, 1),
            is_enabled=True,
            is_active=True,
        )

    @patch("apps.bluesky.sync.list_feed_post_records")
    def test_run_sync_skips_when_source_lock_is_already_held(self, mock_list_feed_post_records):
        self.source_settings.sync_lock_token = "existing-lock"
        self.source_settings.sync_lock_expires_at = timezone.now() + timedelta(minutes=5)
        self.source_settings.save(update_fields=["sync_lock_token", "sync_lock_expires_at"])

        result = run_sync(limit=100)

        self.assertEqual(result, {"imported": 0, "updated": 0, "removed": 0, "skipped": 1, "failed": 0})
        mock_list_feed_post_records.assert_not_called()

    @patch("apps.bluesky.sync.list_feed_post_records")
    def test_run_sync_releases_lock_when_sync_errors(self, mock_list_feed_post_records):
        mock_list_feed_post_records.side_effect = RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            run_sync(limit=100)

        self.source_settings.refresh_from_db()
        self.assertIsNone(self.source_settings.sync_lock_token)
        self.assertIsNone(self.source_settings.sync_lock_expires_at)
