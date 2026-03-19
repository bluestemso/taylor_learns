from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.test import SimpleTestCase

from apps.bluesky.models import BlueskySourceSettings


class TestBlueskySourceSettingsContract(SimpleTestCase):
    def test_model_has_single_active_constraint_name(self):
        constraint_names = [constraint.name for constraint in BlueskySourceSettings._meta.constraints]
        self.assertIn("unique_active_bluesky_source", constraint_names)

    def test_backfill_start_date_is_required(self):
        field = BlueskySourceSettings._meta.get_field("backfill_start_date")
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_effective_backfill_start_at_returns_site_timezone_midnight(self):
        settings_obj = BlueskySourceSettings(
            handle="taylorlearns.com",
            did="did:plc:abc123",
            profile_url="https://bsky.app/profile/taylorlearns.com",
            backfill_start_date=date(2024, 1, 1),
        )

        expected = datetime(2024, 1, 1, 0, 0, 0, tzinfo=ZoneInfo(settings.TIME_ZONE))
        self.assertEqual(settings_obj.effective_backfill_start_at(), expected)
