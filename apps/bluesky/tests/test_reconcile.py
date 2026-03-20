from datetime import date
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from wagtail.models import Page

from apps.bluesky.client import LIST_RECORDS_URL, list_feed_post_records
from apps.bluesky.models import BlueskyPostMap, BlueskySourceSettings
from apps.bluesky.reconcile import classify_record_operation, get_missing_mapped_uris
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


class TestMissingMappedUrisContract(TestCase):
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

        self.first_post = MicroPostPage(title="First", slug="first", date=date(2024, 1, 1), body=[])
        blog_index.add_child(instance=self.first_post)
        self.first_post.save_revision().publish()

        self.second_post = MicroPostPage(title="Second", slug="second", date=date(2024, 1, 2), body=[])
        blog_index.add_child(instance=self.second_post)
        self.second_post.save_revision().publish()

        self.removed_post = MicroPostPage(title="Removed", slug="removed", date=date(2024, 1, 3), body=[])
        blog_index.add_child(instance=self.removed_post)
        self.removed_post.save_revision().publish()

        self.indexed_at = timezone.now()

    def test_returns_only_mapped_uris_missing_from_remote_and_not_already_removed(self):
        missing_uri = "at://did:plc:abc123/app.bsky.feed.post/missing"
        present_uri = "at://did:plc:abc123/app.bsky.feed.post/present"
        previously_removed_uri = "at://did:plc:abc123/app.bsky.feed.post/already-removed"

        BlueskyPostMap.objects.create(
            source_settings=self.source_settings,
            micro_post=self.first_post,
            source_uri=missing_uri,
            source_cid="cid-missing",
            source_did="did:plc:abc123",
            source_rkey="missing",
            source_indexed_at=self.indexed_at,
        )
        BlueskyPostMap.objects.create(
            source_settings=self.source_settings,
            micro_post=self.second_post,
            source_uri=present_uri,
            source_cid="cid-present",
            source_did="did:plc:abc123",
            source_rkey="present",
            source_indexed_at=self.indexed_at,
        )
        BlueskyPostMap.objects.create(
            source_settings=self.source_settings,
            micro_post=self.removed_post,
            source_uri=previously_removed_uri,
            source_cid="cid-removed",
            source_did="did:plc:abc123",
            source_rkey="already-removed",
            source_indexed_at=self.indexed_at,
            removed_at=timezone.now(),
        )

        missing_uris = get_missing_mapped_uris(
            source_settings=self.source_settings,
            remote_uris=[present_uri],
        )

        self.assertEqual(missing_uris, [missing_uri])
