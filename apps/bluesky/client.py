import httpx

LIST_RECORDS_URL = "https://public.api.bsky.app/xrpc/com.atproto.repo.listRecords"


def list_feed_post_records(*, source_settings, cursor: str | None = None, limit: int = 100) -> dict[str, object]:
    params: dict[str, str | int] = {
        "repo": source_settings.did,
        "collection": "app.bsky.feed.post",
        "limit": limit,
    }
    if cursor is not None:
        params["cursor"] = cursor

    response = httpx.get(
        "https://public.api.bsky.app/xrpc/com.atproto.repo.listRecords",
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return {
        "records": payload.get("records", []),
        "cursor": payload.get("cursor"),
    }
