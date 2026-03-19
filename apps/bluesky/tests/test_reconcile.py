from datetime import date
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from wagtail.models import Page

from apps.bluesky.client import LIST_RECORDS_URL, list_feed_post_records
from apps.bluesky.models import BlueskyPostMap, BlueskySourceSettings
from apps.bluesky.reconcile import classify_record_operation
from apps.content.models import BlogIndexPage, MicroPostPage


class TestListFeedPostRecordsContract(TestCase):
    def setUp(self):
        self.source_settings = BlueskySourceSettings.objects.create(
            handle="taylorlearns.com",
            did="did:plc:abc123",
            profile_url="https://bsky.app/profile/taylorlearns.com",
            backfill_start_date=date(2024, 1, 1),
            is_enabled=True,
            is_active=True,
        )

    @patch("apps.bluesky.client.httpx.get")
    def test_list_feed_post_records_calls_list_records_endpoint_contract(self, mock_get):
        mock_get.return_value.json.return_value = {
            "records": [{"uri": "at://did:plc:abc123/app.bsky.feed.post/abc", "cid": "cid-v1", "value": {}}],
            "cursor": "next-cursor",
        }
        mock_get.return_value.raise_for_status.return_value = None

        result = list_feed_post_records(source_settings=self.source_settings, cursor="cursor-1", limit=25)

        mock_get.assert_called_once_with(
            LIST_RECORDS_URL,
            params={
                "repo": "did:plc:abc123",
                "collection": "app.bsky.feed.post",
                "limit": 25,
                "cursor": "cursor-1",
            },
            timeout=30,
        )
        self.assertEqual(result["cursor"], "next-cursor")
        self.assertEqual(len(result["records"]), 1)


class TestClassifyRecordOperationContract(TestCase):
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
        blog_index = BlogIndexPage(title="Blog", slug="blog")
        root.add_child(instance=blog_index)
        blog_index.save_revision().publish()
        self.micro_post = MicroPostPage(title="Existing", slug="existing", date=date(2024, 1, 1), body=[])
        blog_index.add_child(instance=self.micro_post)
        self.micro_post.save_revision().publish()
        self.indexed_at = timezone.now()

    def test_returns_created_when_map_is_missing(self):
        operation = classify_record_operation(
            source_uri="at://did:plc:abc123/app.bsky.feed.post/new-rkey",
            source_cid="cid-v1",
        )

        self.assertEqual(operation, "created")

    def test_returns_updated_when_cid_changes(self):
        BlueskyPostMap.objects.create(
            source_settings=self.source_settings,
            micro_post=self.micro_post,
            source_uri="at://did:plc:abc123/app.bsky.feed.post/existing-rkey",
            source_cid="cid-v1",
            source_did="did:plc:abc123",
            source_rkey="existing-rkey",
            source_indexed_at=self.indexed_at,
        )

        operation = classify_record_operation(
            source_uri="at://did:plc:abc123/app.bsky.feed.post/existing-rkey",
            source_cid="cid-v2",
        )

        self.assertEqual(operation, "updated")

    def test_returns_skipped_when_cid_matches(self):
        BlueskyPostMap.objects.create(
            source_settings=self.source_settings,
            micro_post=self.micro_post,
            source_uri="at://did:plc:abc123/app.bsky.feed.post/existing-rkey",
            source_cid="cid-v1",
            source_did="did:plc:abc123",
            source_rkey="existing-rkey",
            source_indexed_at=self.indexed_at,
        )

        operation = classify_record_operation(
            source_uri="at://did:plc:abc123/app.bsky.feed.post/existing-rkey",
            source_cid="cid-v1",
        )

        self.assertEqual(operation, "skipped")
