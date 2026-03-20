from django.db import transaction
from django.utils import timezone

from apps.bluesky.models import BlueskyPostMap
from apps.bluesky.transform import build_micropost_stream_body
from apps.content.models import BlogIndexPage, MicroPostPage


def upsert_and_publish_micro_post(
    *,
    source_settings,
    source_uri: str,
    source_cid: str,
    source_did: str,
    source_rkey: str,
    source_indexed_at,
    post_text: str,
    post_facets: list[dict] | None,
) -> dict[str, str]:
    parent = BlogIndexPage.objects.live().order_by("id").first()
    if parent is None:
        raise ValueError("No live BlogIndexPage available for Bluesky import")

    with transaction.atomic():
        post_map = BlueskyPostMap.objects.select_related("micro_post").filter(source_uri=source_uri).first()

        if post_map is not None and post_map.source_cid == source_cid:
            return {"operation": "skipped"}

        stream_body = build_micropost_stream_body(text=post_text, facets=post_facets)

        if post_map is None:
            micro_post = MicroPostPage(
                slug=f"bluesky-{source_rkey}",
                title=f"Bluesky {source_rkey}",
                date=source_indexed_at.date(),
                body=stream_body,
            )
            parent.add_child(instance=micro_post)
            micro_post.save()
            micro_post.save_revision().publish()

            BlueskyPostMap.objects.create(
                source_settings=source_settings,
                micro_post=micro_post,
                source_uri=source_uri,
                source_cid=source_cid,
                source_did=source_did,
                source_rkey=source_rkey,
                source_indexed_at=source_indexed_at,
            )
            return {"operation": "created"}

        micro_post = post_map.micro_post
        micro_post.date = source_indexed_at.date()
        micro_post.body = stream_body
        micro_post.save()
        micro_post.save_revision().publish()

        post_map.source_settings = source_settings
        post_map.micro_post = micro_post
        post_map.source_cid = source_cid
        post_map.source_did = source_did
        post_map.source_rkey = source_rkey
        post_map.source_indexed_at = source_indexed_at
        post_map.removed_at = None
        post_map.save(
            update_fields=[
                "source_settings",
                "micro_post",
                "source_cid",
                "source_did",
                "source_rkey",
                "source_indexed_at",
                "removed_at",
                "updated_at",
            ]
        )

    return {"operation": "updated"}


def unpublish_mapped_micro_post(*, source_settings, source_uri: str) -> dict[str, str]:
    post_map = (
        BlueskyPostMap.objects.select_related("micro_post")
        .filter(source_settings=source_settings, source_uri=source_uri)
        .first()
    )

    if post_map is None or post_map.removed_at is not None:
        return {"operation": "skipped"}

    with transaction.atomic():
        micro_post = post_map.micro_post
        micro_post.unpublish(set_expired=False, log_action=True)
        post_map.removed_at = timezone.now()
        post_map.save(update_fields=["removed_at", "updated_at"])

    return {"operation": "removed"}
