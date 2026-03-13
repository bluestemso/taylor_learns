from pathlib import Path

from django.test import SimpleTestCase


class TestTopNavTemplate(SimpleTestCase):
    def test_desktop_nav_uses_feed_portfolio_gadgets_profile_order(self):
        template = self._top_nav_template_contents()
        desktop_nav = self._block_contents(template, "desktop_nav")

        self.assertNotIn('{% translate "Index" %}', template)
        self._assert_ordered(
            desktop_nav,
            [
                '{% translate "Feed" %}',
                '{% translate "Portfolio" %}',
                '{% translate "Gadgets" %}',
                '{% translate "Profile" %}',
            ],
        )

    def test_mobile_nav_uses_feed_portfolio_gadgets_profile_order(self):
        template = self._top_nav_template_contents()
        mobile_nav = self._block_contents(template, "mobile_nav")

        self._assert_ordered(
            mobile_nav,
            [
                '{% translate "Feed" %}',
                '{% translate "Portfolio" %}',
                '{% translate "Gadgets" %}',
                '{% translate "Profile" %}',
            ],
        )

    def _top_nav_template_contents(self) -> str:
        base_dir = Path(__file__).resolve().parents[3]
        return (base_dir / "templates/web/components/top_nav.html").read_text()

    def _block_contents(self, text: str, block_name: str) -> str:
        start_marker = f"{{% block {block_name} %}}"
        end_marker = "{% endblock %}"
        start_index = text.find(start_marker)
        self.assertNotEqual(start_index, -1)
        end_index = text.find(end_marker, start_index)
        self.assertNotEqual(end_index, -1)
        return text[start_index:end_index]

    def _assert_ordered(self, text: str, snippets: list[str]) -> None:
        cursor = 0
        for snippet in snippets:
            position = text.find(snippet, cursor)
            self.assertNotEqual(position, -1, msg=f"Missing snippet: {snippet}")
            cursor = position + len(snippet)


class TestFooterTemplate(SimpleTestCase):
    def test_footer_uses_feed_portfolio_gadgets_profile_order(self):
        template = self._footer_template_contents()

        self.assertNotIn('{% translate "Index" %}', template)
        self._assert_ordered(
            template,
            [
                '{% translate "Feed" %}',
                '{% translate "Portfolio" %}',
                '{% translate "Gadgets" %}',
                '{% translate "Profile" %}',
            ],
        )

    def _footer_template_contents(self) -> str:
        base_dir = Path(__file__).resolve().parents[3]
        return (base_dir / "templates/web/components/footer.html").read_text()

    def _assert_ordered(self, text: str, snippets: list[str]) -> None:
        cursor = 0
        for snippet in snippets:
            position = text.find(snippet, cursor)
            self.assertNotEqual(position, -1, msg=f"Missing snippet: {snippet}")
            cursor = position + len(snippet)


class TestGadgetsIndexTemplate(SimpleTestCase):
    def test_gadgets_index_desktop_nav_uses_feed_portfolio_gadgets_profile_order(self):
        template = self._gadgets_index_template_contents()
        desktop_nav = self._section_between(
            template,
            '<nav class="hidden items-center gap-6 text-xs md:flex">',
            "      </nav>",
        )

        self.assertNotIn('{% translate "Index" %}', template)
        self._assert_ordered(
            desktop_nav,
            [
                'href="{{ blog_url }}">{% translate "Feed" %}</a>',
                'href="{{ portfolio_url }}">{% translate "Portfolio" %}</a>',
                'href="{% url "index" %}">{% translate "Gadgets" %}</a>',
                'href="{{ profile_url }}">{% translate "Profile" %}</a>',
            ],
        )

    def test_gadgets_index_mobile_nav_uses_feed_portfolio_gadgets_profile_order(self):
        template = self._gadgets_index_template_contents()
        mobile_nav = self._section_between(
            template,
            '<div class="flex flex-col p-3 text-[11px]">',
            "            </div>",
        )

        self._assert_ordered(
            mobile_nav,
            [
                'href="{{ blog_url }}">{% translate "Feed" %}</a>',
                'href="{{ portfolio_url }}">{% translate "Portfolio" %}</a>',
                'href="{% url "index" %}">{% translate "Gadgets" %}</a>',
                'href="{{ profile_url }}">{% translate "Profile" %}</a>',
            ],
        )

    def _gadgets_index_template_contents(self) -> str:
        base_dir = Path(__file__).resolve().parents[3]
        return (base_dir / "apps/gadgets/templates/gadgets/index.html").read_text()

    def _section_between(self, text: str, start_marker: str, end_marker: str) -> str:
        start_index = text.find(start_marker)
        self.assertNotEqual(start_index, -1)
        end_index = text.find(end_marker, start_index)
        self.assertNotEqual(end_index, -1)
        return text[start_index:end_index]

    def _assert_ordered(self, text: str, snippets: list[str]) -> None:
        cursor = 0
        for snippet in snippets:
            position = text.find(snippet, cursor)
            self.assertNotEqual(position, -1, msg=f"Missing snippet: {snippet}")
            cursor = position + len(snippet)
