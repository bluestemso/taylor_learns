from pathlib import Path

from django.test import SimpleTestCase


class TestThemeTemplate(SimpleTestCase):
    def test_base_template_uses_theme_preference_cookie_fallback(self):
        base_template = self._base_template_contents()
        self.assertIn("getCookieValue('theme_preference')", base_template)

    def test_base_template_supports_configurable_cookie_domain(self):
        base_template = self._base_template_contents()
        self.assertIn("themeCookieDomain", base_template)
        self.assertIn("domain=${themeCookieDomain}", base_template)

    def _base_template_contents(self) -> str:
        base_dir = Path(__file__).resolve().parents[3]
        return (base_dir / "templates/web/base.html").read_text()
