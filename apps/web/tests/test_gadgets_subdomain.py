from django.test import SimpleTestCase


class TestGadgetsSubdomain(SimpleTestCase):
    def test_gadgets_subdomain_homepage(self):
        response = self.client.get("/", HTTP_HOST="gadgets.taylorlearns.com")
        self.assertContains(response, "Gadgets")
        self.assertContains(response, "Tmux Dojo")

    def test_tmux_dojo_gadget_page(self):
        response = self.client.get("/tmux-dojo/", HTTP_HOST="gadgets.taylorlearns.com")
        self.assertContains(response, "Tmux Shortcut Dojo")

    def test_tmux_dojo_assets_are_served_from_gadget_directory(self):
        response = self.client.get("/tmux-dojo/styles.css", HTTP_HOST="gadgets.taylorlearns.com")
        content = b"".join(getattr(response, "streaming_content", [])).decode()
        self.assertIn("--bg", content)

    def test_tmux_dojo_html_uses_relative_asset_paths(self):
        response = self.client.get("/tmux-dojo/", HTTP_HOST="gadgets.taylorlearns.com")
        content = b"".join(getattr(response, "streaming_content", [])).decode()
        self.assertIn("./styles.css", content)
        self.assertIn("./app.js", content)
