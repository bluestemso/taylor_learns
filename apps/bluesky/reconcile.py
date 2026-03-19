from apps.bluesky.models import BlueskyPostMap


def classify_record_operation(*, source_uri: str, source_cid: str) -> str:
    post_map = BlueskyPostMap.objects.filter(source_uri=source_uri).first()
    if post_map is None:
        return "created"

    if post_map.source_cid != source_cid:
        return "updated"

    return "skipped"
