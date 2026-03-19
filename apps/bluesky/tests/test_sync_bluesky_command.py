from datetime import date
from unittest.mock import call, patch

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from wagtail.models import Page

from apps.bluesky.models import BlueskySourceSettings
from apps.bluesky.sync import run_sync
from apps.content.models import BlogIndexPage, MicroPostPage


class TestRunSyncContract(TestCase):
    def setUp(self):
        self.source_settings = BlueskySourceSettings.objects.create(
            handle="taylorlearns.com",
            did="did:plc:abc123",
            profile_url="https://bsky.app/profile/taylorlearns.com",
            backfill_start_date=date(2024, 1, 1),
            is_enabled=True,
            is_active=True,
        )

    def test_run_sync_raises_when_no_active_enabled_source(self):
        BlueskySourceSettings.objects.all().delete()

        with self.assertRaisesMessage(ValueError, "No active enabled Bluesky source configured"):
            run_sync()

    @patch("apps.bluesky.sync.upsert_and_publish_micro_post")
    @patch("apps.bluesky.sync.classify_record_operation")
    @patch("apps.bluesky.sync.list_feed_post_records")
    def test_run_sync_classifies_before_publish_and_only_publishes_created_or_updated(
        self,
        mock_list_feed_post_records,
        mock_classify_record_operation,
        mock_upsert_and_publish_micro_post,
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
                {
                    "uri": "at://did:plc:abc123/app.bsky.feed.post/c",
                    "cid": "cid-c",
                    "indexedAt": "2024-01-01T02:00:00Z",
                    "value": {"text": "C", "facets": []},
                },
            ],
            "cursor": None,
        }
        mock_classify_record_operation.side_effect = ["created", "updated", "skipped"]

        result = run_sync(limit=3)

        mock_classify_record_operation.assert_has_calls(
            [
                call(source_uri="at://did:plc:abc123/app.bsky.feed.post/a", source_cid="cid-a"),
                call(source_uri="at://did:plc:abc123/app.bsky.feed.post/b", source_cid="cid-b"),
                call(source_uri="at://did:plc:abc123/app.bsky.feed.post/c", source_cid="cid-c"),
            ]
        )
        self.assertEqual(mock_upsert_and_publish_micro_post.call_count, 2)
        self.assertEqual(result, {"imported": 1, "updated": 1, "skipped": 1, "failed": 0})

    @patch("apps.bluesky.sync.list_feed_post_records")
    def test_run_sync_twice_with_unchanged_cid_is_idempotent(self, mock_list_feed_post_records):
        root = Page.get_first_root_node()
        blog_index = BlogIndexPage(title="Blog", slug="blog")
        root.add_child(instance=blog_index)
        blog_index.save_revision().publish()

        mock_list_feed_post_records.return_value = {
            "records": [
                {
                    "uri": "at://did:plc:abc123/app.bsky.feed.post/idempotent",
                    "cid": "cid-idempotent",
                    "indexedAt": "2024-01-01T00:00:00Z",
                    "value": {"text": "same", "facets": []},
                }
            ],
            "cursor": None,
        }

        first = run_sync(limit=1)
        second = run_sync(limit=1)

        self.assertEqual(first, {"imported": 1, "updated": 0, "skipped": 0, "failed": 0})
        self.assertEqual(second, {"imported": 0, "updated": 0, "skipped": 1, "failed": 0})
        self.assertEqual(MicroPostPage.objects.count(), 1)

    @patch("apps.bluesky.sync.upsert_and_publish_micro_post")
    @patch("apps.bluesky.sync.classify_record_operation")
    @patch("apps.bluesky.sync.list_feed_post_records")
    def test_run_sync_counter_mapping_is_explicit_and_deterministic(
        self,
        mock_list_feed_post_records,
        mock_classify_record_operation,
        mock_upsert_and_publish_micro_post,
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
                {
                    "uri": "at://did:plc:abc123/app.bsky.feed.post/c",
                    "cid": "cid-c",
                    "indexedAt": "2024-01-01T02:00:00Z",
                    "value": {"text": "C", "facets": []},
                },
                {
                    "uri": "at://did:plc:abc123/app.bsky.feed.post/d",
                    "cid": "cid-d",
                    "indexedAt": "2024-01-01T03:00:00Z",
                    "value": {"text": "D", "facets": []},
                },
            ],
            "cursor": None,
        }
        mock_classify_record_operation.side_effect = ["created", "updated", "skipped", Exception("boom")]

        result = run_sync(limit=4)

        self.assertEqual(result, {"imported": 1, "updated": 1, "skipped": 1, "failed": 1})
        self.assertEqual(mock_upsert_and_publish_micro_post.call_count, 2)


class TestSyncBlueskyCommand(SimpleTestCase):
    @patch("apps.bluesky.management.commands.sync_bluesky.run_sync")
    def test_sync_bluesky_forwards_limit_and_prints_deterministic_counters(self, mock_run_sync):
        mock_run_sync.return_value = {"imported": 3, "updated": 2, "skipped": 5, "failed": 1}

        with patch("sys.stdout"):
            output = []

            def capture_write(message):
                output.append(str(message))

            with patch("django.core.management.base.OutputWrapper.write", side_effect=capture_write):
                call_command("sync_bluesky", "--limit", "25")

        mock_run_sync.assert_called_once_with(limit=25)
        rendered = " ".join(output)
        self.assertIn("Sync complete: imported=3 updated=2 skipped=5 failed=1", rendered)
