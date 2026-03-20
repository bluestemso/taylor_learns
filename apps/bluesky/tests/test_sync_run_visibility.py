from datetime import date
from unittest.mock import patch

from django.contrib import admin
from django.test import TestCase

from apps.bluesky.admin import BlueskySyncRunAdmin
from apps.bluesky.models import BlueskySourceSettings, BlueskySyncRun
from apps.bluesky.sync import run_sync


class TestRunSyncVisibility(TestCase):
    def setUp(self):
        self.source_settings = BlueskySourceSettings.objects.create(
            handle="taylorlearns.com",
            did="did:plc:abc123",
            profile_url="https://bsky.app/profile/taylorlearns.com",
            backfill_start_date=date(2024, 1, 1),
            is_enabled=True,
            is_active=True,
        )

    @patch("apps.bluesky.sync.get_missing_mapped_uris", return_value=[])
    @patch("apps.bluesky.sync.upsert_and_publish_micro_post")
    @patch("apps.bluesky.sync.classify_record_operation")
    @patch("apps.bluesky.sync.list_feed_post_records")
    def test_run_sync_persists_one_run_with_expected_counters(
        self,
        mock_list_feed_post_records,
        mock_classify_record_operation,
        mock_upsert_and_publish_micro_post,
        _mock_get_missing_mapped_uris,
    ):
        mock_list_feed_post_records.return_value = {
            "records": [
                {
                    "uri": "at://did:plc:abc123/app.bsky.feed.post/a",
                    "cid": "cid-a",
                    "indexedAt": "2024-01-01T00:00:00Z",
                    "value": {"text": "A", "facets": []},
                },
                {
                    "uri": "at://did:plc:abc123/app.bsky.feed.post/b",
                    "cid": "cid-b",
                    "indexedAt": "2024-01-01T01:00:00Z",
                    "value": {"text": "B", "facets": []},
                },
            ],
            "cursor": None,
        }
        mock_classify_record_operation.side_effect = ["created", "skipped"]

        result = run_sync(limit=2)

        self.assertEqual(result, {"imported": 1, "updated": 0, "removed": 0, "skipped": 1, "failed": 0})
        self.assertEqual(mock_upsert_and_publish_micro_post.call_count, 1)
        self.assertEqual(BlueskySyncRun.objects.count(), 1)

        run = BlueskySyncRun.objects.get()
        self.assertEqual(run.source_settings, self.source_settings)
        self.assertEqual(run.imported_count, 1)
        self.assertEqual(run.updated_count, 0)
        self.assertEqual(run.removed_count, 0)
        self.assertEqual(run.skipped_count, 1)
        self.assertEqual(run.failed_count, 0)
        self.assertIsNotNone(run.started_at)
        self.assertIsNotNone(run.completed_at)


class TestRunVisibilityAdminContract(TestCase):
    def test_run_model_is_registered_for_admin_inspection(self):
        self.assertIn(BlueskySyncRun, admin.site._registry)

        model_admin = admin.site._registry[BlueskySyncRun]
        self.assertIsInstance(model_admin, BlueskySyncRunAdmin)
        self.assertEqual(
            model_admin.list_display,
            (
                "source_handle",
                "completed_at",
                "imported_count",
                "updated_count",
                "removed_count",
                "skipped_count",
                "failed_count",
            ),
        )
