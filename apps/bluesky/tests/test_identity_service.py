from unittest.mock import Mock, patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from apps.bluesky.services.identity import resolve_handle_identity


class TestResolveHandleIdentityContract(SimpleTestCase):
    @patch("apps.bluesky.services.identity.httpx.get")
    def test_resolves_handle_and_did_with_expected_endpoint(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "did": "did:plc:abc123",
            "handle": "taylorlearns.com",
        }
        mock_get.return_value = response

        resolved = resolve_handle_identity("taylorlearns.com")

        mock_get.assert_called_once_with(
            "https://public.api.bsky.app/xrpc/com.atproto.identity.resolveHandle",
            params={"handle": "taylorlearns.com"},
            timeout=10,
        )
        self.assertEqual(resolved["handle"], "taylorlearns.com")
        self.assertEqual(resolved["did"], "did:plc:abc123")
        self.assertEqual(resolved["profile_url"], "https://bsky.app/profile/taylorlearns.com")

    @patch("apps.bluesky.services.identity.httpx.get")
    def test_raises_validation_error_when_did_missing(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"handle": "taylorlearns.com"}
        mock_get.return_value = response

        with self.assertRaises(ValidationError):
            resolve_handle_identity("taylorlearns.com")

    @patch("apps.bluesky.services.identity.httpx.get")
    def test_raises_validation_error_when_non_2xx(self, mock_get):
        mock_get.side_effect = Exception("boom")

        with self.assertRaises(ValidationError):
            resolve_handle_identity("taylorlearns.com")

    @patch("apps.bluesky.services.identity.httpx.get")
    def test_raises_validation_error_when_timeout(self, mock_get):
        mock_get.side_effect = TimeoutError("timeout")

        with self.assertRaises(ValidationError):
            resolve_handle_identity("taylorlearns.com")
