from django.utils.dateparse import parse_datetime

from apps.bluesky.client import list_feed_post_records
from apps.bluesky.models import BlueskySourceSettings
from apps.bluesky.publish import unpublish_mapped_micro_post, upsert_and_publish_micro_post
from apps.bluesky.reconcile import classify_record_operation, get_missing_mapped_uris


def run_sync(*, limit: int = 100) -> dict[str, int]:
    source_settings = (
        BlueskySourceSettings.objects.filter(is_active=True, is_enabled=True).order_by("-updated_at").first()
    )
    if source_settings is None:
        raise ValueError("No active enabled Bluesky source configured")

    counters = {"imported": 0, "updated": 0, "removed": 0, "skipped": 0, "failed": 0}
    payload = list_feed_post_records(source_settings=source_settings, limit=limit)
    records = payload.get("records", [])
    if not isinstance(records, list):
        records = []
    remote_uris: set[str] = set()

    for record in records:
        try:
            source_uri = str(record.get("uri", "")).strip()
            source_cid = str(record.get("cid", "")).strip()
            remote_uris.add(source_uri)
            value = record.get("value") or {}
            source_indexed_at_raw = str(record.get("indexedAt") or value.get("createdAt") or "").strip()
            source_indexed_at = parse_datetime(source_indexed_at_raw)
            if source_indexed_at is None:
                raise ValueError("Record missing or invalid timestamp")

            post_text = str(value.get("text", ""))
            post_facets = value.get("facets") if isinstance(value.get("facets"), list) else []
            source_rkey = source_uri.rsplit("/", 1)[-1] if source_uri else ""

            operation = classify_record_operation(source_uri=source_uri, source_cid=source_cid)

            if operation in {"created", "updated"}:
                upsert_and_publish_micro_post(
                    source_settings=source_settings,
                    source_uri=source_uri,
                    source_cid=source_cid,
                    source_did=source_settings.did,
                    source_rkey=source_rkey,
                    source_indexed_at=source_indexed_at,
                    post_text=post_text,
                    post_facets=post_facets,
                )

            if operation == "created":
                counters["imported"] += 1
            elif operation == "updated":
                counters["updated"] += 1
            elif operation == "skipped":
                counters["skipped"] += 1
            else:
                counters["failed"] += 1
        except Exception:  # noqa: BLE001
            counters["failed"] += 1

    missing_mapped_uris = get_missing_mapped_uris(source_settings=source_settings, remote_uris=list(remote_uris))
    for source_uri in missing_mapped_uris:
        try:
            result = unpublish_mapped_micro_post(source_settings=source_settings, source_uri=source_uri)
            if result.get("operation") == "removed":
                counters["removed"] += 1
        except Exception:  # noqa: BLE001
            counters["failed"] += 1

    return counters
