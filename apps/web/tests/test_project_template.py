from pathlib import Path

from django.test import SimpleTestCase


class TestProjectTemplate(SimpleTestCase):
    def test_project_page_uses_cohesive_case_study_layout(self):
        template = self._project_template_contents()

        self.assertIn('{% translate "Back to Portfolio" %}', template)
        self.assertIn('href="{{ page.get_parent.url }}"', template)
        self.assertIn("{% with image_count=page.project_images.count %}", template)
        self.assertIn("{% if image_count == 1 %}", template)
        self.assertIn('class="ei-case-reading">{% include_block page.body %}</div>', template)

    def test_site_css_defines_case_reading_typography(self):
        css = self._site_tailwind_contents()

        self.assertIn(".ei-case-reading h2,", css)
        self.assertIn(".ei-case-reading h3,", css)
        self.assertIn(".ei-case-reading ul,", css)

    def _project_template_contents(self) -> str:
        base_dir = Path(__file__).resolve().parents[3]
        return (base_dir / "templates/content/project_page.html").read_text()

    def _site_tailwind_contents(self) -> str:
        base_dir = Path(__file__).resolve().parents[3]
        return (base_dir / "assets/styles/site-tailwind.css").read_text()
