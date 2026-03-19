from datetime import date
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.bluesky.admin import BlueskySourceSettingsAdmin
from apps.bluesky.models import BlueskySourceSettings
from apps.users.models import CustomUser


class TestBlueskySourceSettingsAdminFlow(TestCase):
    def setUp(self):
        self.superuser = CustomUser.objects.create_superuser(
            username="admin@example.com",
            email="admin@example.com",
            password="pass12345",
        )
        self.user = CustomUser.objects.create_user(
            username="user@example.com",
            email="user@example.com",
            password="pass12345",
        )

    @patch("apps.bluesky.forms.resolve_handle_identity")
    def test_superuser_save_resolves_identity_and_persists_canonical_values(self, mock_resolve):
        mock_resolve.return_value = {
            "handle": "taylorlearns.com",
            "did": "did:plc:abc123",
            "profile_url": "https://bsky.app/profile/taylorlearns.com",
        }
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("admin:bluesky_blueskysourcesettings_add"),
            {
                "handle": "taylorlearns.com",
                "backfill_start_date": "2024-01-01",
                "is_enabled": "on",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        saved = BlueskySourceSettings.objects.get()
        self.assertEqual(saved.handle, "taylorlearns.com")
        self.assertEqual(saved.did, "did:plc:abc123")
        self.assertEqual(saved.profile_url, "https://bsky.app/profile/taylorlearns.com")

    @patch("apps.bluesky.forms.resolve_handle_identity")
    def test_verification_failure_shows_form_error_and_does_not_save(self, mock_resolve):
        mock_resolve.side_effect = ValidationError("Unable to verify")
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("admin:bluesky_blueskysourcesettings_add"),
            {
                "handle": "taylorlearns.com",
                "backfill_start_date": "2024-01-01",
                "is_enabled": "on",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unable to verify")
        self.assertEqual(BlueskySourceSettings.objects.count(), 0)

    @patch("apps.bluesky.forms.resolve_handle_identity")
    def test_replacement_requires_confirm_replace_when_identity_changes(self, mock_resolve):
        BlueskySourceSettings.objects.create(
            handle="old.example.com",
            did="did:plc:old",
            profile_url="https://bsky.app/profile/old.example.com",
            backfill_start_date=date(2024, 1, 1),
            is_enabled=True,
            is_active=True,
        )
        mock_resolve.return_value = {
            "handle": "new.example.com",
            "did": "did:plc:new",
            "profile_url": "https://bsky.app/profile/new.example.com",
        }
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("admin:bluesky_blueskysourcesettings_add"),
            {
                "handle": "new.example.com",
                "backfill_start_date": "2024-01-01",
                "is_enabled": "on",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Confirm source replacement to change the active Bluesky source.")
        self.assertEqual(BlueskySourceSettings.objects.count(), 1)

    def test_non_superusers_cannot_add_or_change_source_settings(self):
        admin_obj = BlueskySourceSettingsAdmin(BlueskySourceSettings, AdminSite())
        request = RequestFactory().get("/")
        request.user = self.user

        self.assertFalse(admin_obj.has_add_permission(request))
        self.assertFalse(admin_obj.has_change_permission(request))
