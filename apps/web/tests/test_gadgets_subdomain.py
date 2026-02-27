from urllib.parse import urlsplit

from django.conf import settings
from django.test import SimpleTestCase


class TestGadgetsSubdomain(SimpleTestCase):
    def test_gadgets_subdomain_homepage(self):
        response = self.client.get("/", HTTP_HOST=self._gadgets_host())
        self.assertContains(response, "Gadgets")
        self.assertContains(response, "Tmux Dojo")

    def test_tmux_dojo_gadget_page(self):
        response = self.client.get("/tmux-dojo/", HTTP_HOST=self._gadgets_host())
        self.assertContains(response, "Tmux Shortcut Dojo")

    def test_tmux_dojo_assets_are_served_from_gadget_directory(self):
        response = self.client.get("/tmux-dojo/styles.css", HTTP_HOST=self._gadgets_host())
        content = b"".join(getattr(response, "streaming_content", [])).decode()
        self.assertIn("--bg", content)

    def test_tmux_dojo_html_uses_relative_asset_paths(self):
        response = self.client.get("/tmux-dojo/", HTTP_HOST=self._gadgets_host())
        content = b"".join(getattr(response, "streaming_content", [])).decode()
        self.assertIn("./styles.css", content)
        self.assertIn("./app.js", content)

    def test_gadgets_index_has_navigation_to_main_site(self):
        response = self.client.get("/", HTTP_HOST=self._gadgets_host())
        main_site_url = settings.PROJECT_METADATA["URL"].rstrip("/")
        self.assertContains(response, f'href="{main_site_url}/"')
        self.assertContains(response, f'href="{main_site_url}/portfolio/"')

    def _gadgets_host(self) -> str:
        configured = settings.GADGETS_HOSTS[0]
        parsed = urlsplit(configured if "://" in configured else f"//{configured}")
        return parsed.netloc or configured
