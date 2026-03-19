from html import escape


def _extract_link_spans(*, facets: list[dict] | None, encoded_text: bytes) -> list[tuple[int, int, str]]:
    if not facets:
        return []

    spans: list[tuple[int, int, str]] = []

    for facet in facets:
        index = facet.get("index") or {}
        byte_start = index.get("byteStart")
        byte_end = index.get("byteEnd")

        if not isinstance(byte_start, int) or not isinstance(byte_end, int):
            continue
        if byte_start < 0 or byte_end <= byte_start or byte_end > len(encoded_text):
            continue

        for feature in facet.get("features") or []:
            if feature.get("$type") != "app.bsky.richtext.facet#link":
                continue

            uri = feature.get("uri")
            if isinstance(uri, str) and uri:
                spans.append((byte_start, byte_end, uri))
                break

    spans.sort(key=lambda item: (item[0], item[1]))
    return spans


def render_post_body_html(*, text: str, facets: list[dict] | None) -> str:
    encoded_text = text.encode("utf-8")
    link_spans = _extract_link_spans(facets=facets, encoded_text=encoded_text)

    if not link_spans:
        return escape(text)

    parts: list[str] = []
    cursor = 0

    for byte_start, byte_end, uri in link_spans:
        if byte_start < cursor:
            continue

        plain_bytes = encoded_text[cursor:byte_start]
        link_bytes = encoded_text[byte_start:byte_end]

        try:
            plain_text = plain_bytes.decode("utf-8")
            link_text = link_bytes.decode("utf-8")
        except UnicodeDecodeError:
            continue

        parts.append(escape(plain_text))
        parts.append(f'<a href="{escape(uri, quote=True)}">{escape(link_text)}</a>')
        cursor = byte_end

    trailing_text = encoded_text[cursor:].decode("utf-8")
    parts.append(escape(trailing_text))

    return "".join(parts)


def build_micropost_stream_body(*, text: str, facets: list[dict] | None) -> list[dict]:
    return [{"type": "paragraph", "value": render_post_body_html(text=text, facets=facets)}]
