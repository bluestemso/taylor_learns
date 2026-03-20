from apps.bluesky.models import BlueskyPostMap


def classify_record_operation(*, source_uri: str, source_cid: str) -> str:
    post_map = BlueskyPostMap.objects.filter(source_uri=source_uri).first()
    if post_map is None:
        return "created"

    if post_map.source_cid != source_cid:
        return "updated"

    return "skipped"


def get_missing_mapped_uris(*, source_settings, remote_uris: list[str]) -> list[str]:
    missing_uri_qs = (
        BlueskyPostMap.objects.filter(source_settings=source_settings, removed_at__isnull=True)
        .exclude(source_uri__in=remote_uris)
        .order_by("source_uri")
        .values_list("source_uri", flat=True)
    )
    return list(missing_uri_qs)
