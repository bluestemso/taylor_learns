from urllib.parse import urlsplit

from django.conf import settings
from django.test import TestCase

from apps.gadgets.models import GadgetSource


class TestGadgetVisibilityControls(TestCase):
    def test_hidden_gadget_is_not_listed_but_remains_accessible(self):
        GadgetSource.objects.create(
            slug="tmux-dojo",
            repo_full_name="bluestemso/tmux-dojo",
            is_hidden=True,
        )

        index_response = self.client.get("/", HTTP_HOST=self._gadgets_host())
        self.assertNotContains(index_response, "Tmux Dojo")

        detail_response = self.client.get("/tmux-dojo/", HTTP_HOST=self._gadgets_host())
        self.assertEqual(detail_response.status_code, 200)

    def test_blocked_gadget_is_not_listed_and_returns_not_found(self):
        GadgetSource.objects.create(
            slug="tmux-dojo",
            repo_full_name="bluestemso/tmux-dojo",
            is_blocked=True,
        )

        index_response = self.client.get("/", HTTP_HOST=self._gadgets_host())
        self.assertNotContains(index_response, "Tmux Dojo")

        with self.assertLogs("django.request", level="WARNING"):
            detail_response = self.client.get("/tmux-dojo/", HTTP_HOST=self._gadgets_host())
        self.assertEqual(detail_response.status_code, 404)

        with self.assertLogs("django.request", level="WARNING"):
            asset_response = self.client.get("/tmux-dojo/styles.css", HTTP_HOST=self._gadgets_host())
        self.assertEqual(asset_response.status_code, 404)

    def _gadgets_host(self) -> str:
        configured = settings.GADGETS_HOSTS[0]
        parsed = urlsplit(configured if "://" in configured else f"//{configured}")
        return parsed.netloc or configured
