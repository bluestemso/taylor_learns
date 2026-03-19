from datetime import date

from django.test import TestCase
from django.utils import timezone
from wagtail.models import Page

from apps.bluesky.models import BlueskyPostMap, BlueskySourceSettings
from apps.bluesky.publish import upsert_and_publish_micro_post
from apps.content.models import BlogIndexPage, MicroPostPage


class TestUpsertAndPublishMicroPostContract(TestCase):
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

        self.indexed_at = timezone.now()

    def test_create_path_creates_page_and_map(self):
        result = upsert_and_publish_micro_post(
            source_settings=self.source_settings,
            source_uri="at://did:plc:abc123/app.bsky.feed.post/3k4duf64zgr2m",
            source_cid="cid-v1",
            source_did="did:plc:abc123",
            source_rkey="3k4duf64zgr2m",
            source_indexed_at=self.indexed_at,
            post_text="hello world",
            post_facets=None,
        )

        self.assertEqual(result["operation"], "created")
        self.assertEqual(BlueskyPostMap.objects.count(), 1)
        self.assertEqual(MicroPostPage.objects.count(), 1)

        post_map = BlueskyPostMap.objects.get(source_uri="at://did:plc:abc123/app.bsky.feed.post/3k4duf64zgr2m")
        self.assertEqual(post_map.source_cid, "cid-v1")
        self.assertTrue(post_map.micro_post.live)

    def test_update_path_mutates_existing_page_and_map(self):
        upsert_and_publish_micro_post(
            source_settings=self.source_settings,
            source_uri="at://did:plc:abc123/app.bsky.feed.post/3k4duf64zgr2m",
            source_cid="cid-v1",
            source_did="did:plc:abc123",
            source_rkey="3k4duf64zgr2m",
            source_indexed_at=self.indexed_at,
            post_text="hello world",
            post_facets=None,
        )

        result = upsert_and_publish_micro_post(
            source_settings=self.source_settings,
            source_uri="at://did:plc:abc123/app.bsky.feed.post/3k4duf64zgr2m",
            source_cid="cid-v2",
            source_did="did:plc:abc123",
            source_rkey="3k4duf64zgr2m",
            source_indexed_at=self.indexed_at + timezone.timedelta(hours=1),
            post_text="updated post body",
            post_facets=None,
        )

        self.assertEqual(result["operation"], "updated")
        self.assertEqual(MicroPostPage.objects.count(), 1)

        post_map = BlueskyPostMap.objects.get(source_uri="at://did:plc:abc123/app.bsky.feed.post/3k4duf64zgr2m")
        self.assertEqual(post_map.source_cid, "cid-v2")
        self.assertTrue(post_map.micro_post.live)
        block = post_map.micro_post.body.raw_data[0]
        self.assertEqual(block["type"], "paragraph")
        self.assertEqual(block["value"], "updated post body")

    def test_create_and_update_paths_publish_live_content(self):
        created = upsert_and_publish_micro_post(
            source_settings=self.source_settings,
            source_uri="at://did:plc:abc123/app.bsky.feed.post/3k4duf64zgr2m",
            source_cid="cid-v1",
            source_did="did:plc:abc123",
            source_rkey="3k4duf64zgr2m",
            source_indexed_at=self.indexed_at,
            post_text="created body",
            post_facets=None,
        )
        updated = upsert_and_publish_micro_post(
            source_settings=self.source_settings,
            source_uri="at://did:plc:abc123/app.bsky.feed.post/3k4duf64zgr2m",
            source_cid="cid-v2",
            source_did="did:plc:abc123",
            source_rkey="3k4duf64zgr2m",
            source_indexed_at=self.indexed_at + timezone.timedelta(hours=1),
            post_text="updated body",
            post_facets=None,
        )

        post_map = BlueskyPostMap.objects.get(source_uri="at://did:plc:abc123/app.bsky.feed.post/3k4duf64zgr2m")

        self.assertEqual(created["operation"], "created")
        self.assertEqual(updated["operation"], "updated")
        self.assertTrue(post_map.micro_post.live)

    def test_unchanged_cid_skips_without_creating_new_page(self):
        upsert_and_publish_micro_post(
            source_settings=self.source_settings,
            source_uri="at://did:plc:abc123/app.bsky.feed.post/3k4duf64zgr2m",
            source_cid="cid-v1",
            source_did="did:plc:abc123",
            source_rkey="3k4duf64zgr2m",
            source_indexed_at=self.indexed_at,
            post_text="hello world",
            post_facets=None,
        )

        result = upsert_and_publish_micro_post(
            source_settings=self.source_settings,
            source_uri="at://did:plc:abc123/app.bsky.feed.post/3k4duf64zgr2m",
            source_cid="cid-v1",
            source_did="did:plc:abc123",
            source_rkey="3k4duf64zgr2m",
            source_indexed_at=self.indexed_at + timezone.timedelta(hours=1),
            post_text="this should be ignored",
            post_facets=None,
        )

        operation = result["operation"]
        self.assertTrue(operation == "skipped")
        self.assertEqual(MicroPostPage.objects.count(), 1)
        self.assertEqual(BlueskyPostMap.objects.count(), 1)
