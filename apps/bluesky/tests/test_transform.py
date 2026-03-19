from django.test import SimpleTestCase

from apps.bluesky.transform import build_micropost_stream_body, render_post_body_html


class TestRenderPostBodyHtmlContract(SimpleTestCase):
    def test_plain_text_renders_without_changes(self):
        rendered = render_post_body_html(text="hello world", facets=None)

        self.assertEqual(rendered, "hello world")

    def test_link_facet_renders_anchor_with_canonical_uri(self):
        text = "visit docs"
        facets = [
            {
                "index": {"byteStart": 6, "byteEnd": 10},
                "features": [
                    {
                        "$type": "app.bsky.richtext.facet#link",
                        "uri": "https://docs.example.com/canonical",
                    }
                ],
            }
        ]

        rendered = render_post_body_html(text=text, facets=facets)

        self.assertEqual(
            rendered,
            'visit <a href="https://docs.example.com/canonical">docs</a>',
        )

    def test_utf8_byte_offsets_preserve_non_link_boundaries(self):
        text = "A🙂B docs C"
        encoded = text.encode("utf-8")
        target = "docs".encode("utf-8")
        byte_start = encoded.index(target)
        byte_end = byte_start + len(target)
        facets = [
            {
                "index": {"byteStart": byte_start, "byteEnd": byte_end},
                "features": [
                    {
                        "$type": "app.bsky.richtext.facet#link",
                        "uri": "https://example.com/docs",
                    }
                ],
            }
        ]

        rendered = render_post_body_html(text=text, facets=facets)

        self.assertEqual(rendered, 'A🙂B <a href="https://example.com/docs">docs</a> C')

    def test_absent_facets_escapes_plain_text_and_has_no_anchor(self):
        rendered = render_post_body_html(text="A < B", facets=None)

        self.assertEqual(rendered, "A &lt; B")
        self.assertNotIn("<a ", rendered)

    def test_stream_body_wraps_rendered_html_in_paragraph_block(self):
        body = build_micropost_stream_body(text="hello world", facets=None)

        self.assertEqual(body, [{"type": "paragraph", "value": "hello world"}])
