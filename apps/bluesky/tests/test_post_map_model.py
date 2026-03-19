from datetime import date

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from wagtail.models import Page

from apps.bluesky.models import BlueskyPostMap, BlueskySourceSettings
from apps.content.models import BlogIndexPage, MicroPostPage


class TestBlueskyPostMapModelContract(TestCase):
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

        self.micro_post = MicroPostPage(
            title="Imported post",
            slug="imported-post",
            date=date(2024, 1, 2),
            body=[("paragraph", "Hello from Bluesky")],
        )
        self.blog_index.add_child(instance=self.micro_post)

    def test_duplicate_source_uri_raises_integrity_error(self):
        BlueskyPostMap.objects.create(
            source_settings=self.source_settings,
            micro_post=self.micro_post,
            source_uri="at://did:plc:abc123/app.bsky.feed.post/3k4duf64zgr2m",
            source_cid="bafyrei123",
            source_did="did:plc:abc123",
            source_rkey="3k4duf64zgr2m",
            source_indexed_at=timezone.now(),
        )

        with self.assertRaises(IntegrityError):
            BlueskyPostMap.objects.create(
                source_settings=self.source_settings,
                micro_post=self.micro_post,
                source_uri="at://did:plc:abc123/app.bsky.feed.post/3k4duf64zgr2m",
                source_cid="bafyrei456",
                source_did="did:plc:abc123",
                source_rkey="3k4duf64zgr2m",
                source_indexed_at=timezone.now(),
            )

    def test_source_identity_and_micro_post_fields_are_required(self):
        required_fields = [
            "source_uri",
            "source_cid",
            "source_did",
            "source_rkey",
            "source_indexed_at",
            "micro_post",
        ]

        for field_name in required_fields:
            field = BlueskyPostMap._meta.get_field(field_name)
            self.assertFalse(field.null, msg=f"{field_name} must be required")
            self.assertFalse(field.blank, msg=f"{field_name} must be required")

    def test_map_links_source_settings_and_micropost_models(self):
        source_settings_field = BlueskyPostMap._meta.get_field("source_settings")
        micro_post_field = BlueskyPostMap._meta.get_field("micro_post")

        self.assertEqual(source_settings_field.remote_field.model, BlueskySourceSettings)
        self.assertEqual(micro_post_field.remote_field.model, MicroPostPage)
        self.assertEqual(source_settings_field.remote_field.related_name, "post_maps")
        self.assertEqual(micro_post_field.remote_field.related_name, "bluesky_post_maps")

    def test_model_ordering_matches_source_index_recency(self):
        self.assertEqual(BlueskyPostMap._meta.ordering, ["-source_indexed_at", "-updated_at"])

    def test_constraint_name_for_unique_source_uri_is_present(self):
        constraint_names = [constraint.name for constraint in BlueskyPostMap._meta.constraints]
        self.assertIn("unique_bluesky_post_map_source_uri", constraint_names)
