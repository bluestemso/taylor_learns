from pathlib import Path

from django.test import SimpleTestCase


class TestFooterTemplate(SimpleTestCase):
    def test_footer_does_not_render_terms_link(self):
        template = self._footer_template_contents()

        self.assertNotIn('{% translate "Terms" %}', template)

    def test_footer_uses_compact_single_line_brand_and_copyright(self):
        template = self._footer_template_contents()

        self.assertIn(
            "ei-shell flex flex-col gap-4 p-3 md:flex-row md:items-center md:justify-between md:gap-6 md:p-4", template
        )
        self.assertIn("flex items-baseline gap-3", template)
        self.assertNotIn("mt-3 ei-mono", template)

    def _footer_template_contents(self) -> str:
        base_dir = Path(__file__).resolve().parents[3]
        return (base_dir / "templates/web/components/footer.html").read_text()


class TestBlogPageTemplate(SimpleTestCase):
    def test_blog_header_does_not_render_intro(self):
        template = self._blog_template_contents()

        self.assertNotIn('<p class="mt-8 max-w-[52ch] text-xl italic leading-[1.45]">{{ page.intro }}</p>', template)

    def test_blog_body_renders_intro(self):
        template = self._blog_template_contents()

        self.assertIn('<p id="intro">{{ page.intro }}</p>', template)

    def _blog_template_contents(self) -> str:
        base_dir = Path(__file__).resolve().parents[3]
        return (base_dir / "templates/content/blog_page.html").read_text()
