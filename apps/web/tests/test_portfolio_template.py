from pathlib import Path

from django.test import SimpleTestCase


class TestPortfolioTemplate(SimpleTestCase):
    def test_project_cards_use_single_full_card_link(self):
        template = self._portfolio_template_contents()

        self.assertIn('<a class="block h-full" href="{{ project.url }}">', template)
        self.assertIn('[{% translate "View Case" %}]</span>', template)
        self.assertNotIn(
            (
                '<a class="ei-mono text-[11px] group-hover:text-[var(--ei-primary)]" '
                'href="{{ project.url }}">[{% translate "View Case" %}]</a>'
            ),
            template,
        )

    def _portfolio_template_contents(self) -> str:
        base_dir = Path(__file__).resolve().parents[3]
        return (base_dir / "templates/content/portfolio_index_page.html").read_text()
