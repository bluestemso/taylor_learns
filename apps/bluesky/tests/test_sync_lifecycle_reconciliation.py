from datetime import date
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from wagtail.models import Page

from apps.bluesky.models import BlueskyPostMap, BlueskySourceSettings
from apps.bluesky.sync import run_sync
from apps.content.models import BlogIndexPage


class TestRunSyncLifecycleReconciliation(TestCase):
    def setUp(self):
        self.source_settings = BlueskySourceSettings.objects.create(
            handle="taylorlearns.com",
            did="did:plc:abc123",
            profile_url="https://bsky.app/profile/taylorlearns.com",
            backfill_start_date=date(2024, 1, 1),
            is_enabled=True,
            is_active=True,
        )

        root = Page.get_first_root_node()
        self.blog_index = BlogIndexPage(title="Blog", slug="blog")
        root.add_child(instance=self.blog_index)
        self.blog_index.save_revision().publish()

    @patch("apps.bluesky.sync.list_feed_post_records")
    def test_cid_change_updates_existing_mapped_micro_post_body(self, mock_list_feed_post_records):
        base_indexed_at = timezone.now()
        source_uri = "at://did:plc:abc123/app.bsky.feed.post/editable"

        mock_list_feed_post_records.return_value = {
            "records": [
                {
                    "uri": source_uri,
                    "cid": "cid-v1",
                    "indexedAt": base_indexed_at.isoformat(),
                    "value": {"text": "original body", "facets": []},
                }
            ],
            "cursor": None,
        }
        first_result = run_sync(limit=1)

        mock_list_feed_post_records.return_value = {
            "records": [
                {
                    "uri": source_uri,
                    "cid": "cid-v2",
                    "indexedAt": (base_indexed_at + timezone.timedelta(hours=1)).isoformat(),
                    "value": {"text": "edited body", "facets": []},
                }
            ],
            "cursor": None,
        }
        second_result = run_sync(limit=1)

        self.assertEqual(first_result, {"imported": 1, "updated": 0, "removed": 0, "skipped": 0, "failed": 0})
        self.assertEqual(second_result, {"imported": 0, "updated": 1, "removed": 0, "skipped": 0, "failed": 0})

        post_map = BlueskyPostMap.objects.get(source_uri=source_uri)
        block = post_map.micro_post.body.raw_data[0]
        self.assertEqual(block["value"], "edited body")

    @patch("apps.bluesky.sync.list_feed_post_records")
    def test_missing_mapped_uri_triggers_soft_remove_once(self, mock_list_feed_post_records):
        source_uri = "at://did:plc:abc123/app.bsky.feed.post/deleted"
        indexed_at = timezone.now()

        mock_list_feed_post_records.return_value = {
            "records": [
                {
                    "uri": source_uri,
                    "cid": "cid-v1",
                    "indexedAt": indexed_at.isoformat(),
                    "value": {"text": "to be removed", "facets": []},
                }
            ],
            "cursor": None,
        }
        created_result = run_sync(limit=1)
        post_map = BlueskyPostMap.objects.get(source_uri=source_uri)
        self.assertTrue(post_map.micro_post.live)

        mock_list_feed_post_records.return_value = {"records": [], "cursor": None}
        removed_result = run_sync(limit=1)
        post_map.refresh_from_db()

        self.assertEqual(created_result, {"imported": 1, "updated": 0, "removed": 0, "skipped": 0, "failed": 0})
        self.assertEqual(removed_result, {"imported": 0, "updated": 0, "removed": 1, "skipped": 0, "failed": 0})
        self.assertFalse(post_map.micro_post.live)
        self.assertIsNotNone(post_map.removed_at)

        removed_again_result = run_sync(limit=1)
        self.assertEqual(removed_again_result, {"imported": 0, "updated": 0, "removed": 0, "skipped": 0, "failed": 0})
