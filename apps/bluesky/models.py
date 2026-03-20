from datetime import datetime, time
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.utils.models import BaseModel


class BlueskySourceSettings(BaseModel):
    handle = models.CharField(max_length=253)
    did = models.CharField(max_length=255)
    profile_url = models.URLField()
    backfill_start_date = models.DateField()
    is_enabled = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        app_label = "bluesky"
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["is_active"],
                condition=Q(is_active=True),
                name="unique_active_bluesky_source",
            )
        ]

    def effective_backfill_start_at(self) -> datetime:
        return datetime.combine(
            self.backfill_start_date,
            time.min,
            tzinfo=ZoneInfo(settings.TIME_ZONE),
        )


class BlueskyPostMap(BaseModel):
    source_settings = models.ForeignKey(
        "bluesky.BlueskySourceSettings",
        on_delete=models.CASCADE,
        related_name="post_maps",
    )
    micro_post = models.ForeignKey(
        "content.MicroPostPage",
        on_delete=models.CASCADE,
        related_name="bluesky_post_maps",
    )
    source_uri = models.CharField(max_length=512, unique=True)
    source_cid = models.CharField(max_length=128)
    source_did = models.CharField(max_length=255)
    source_rkey = models.CharField(max_length=255)
    source_indexed_at = models.DateTimeField()
    last_synced_at = models.DateTimeField(auto_now=True)
    removed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "bluesky"
        ordering = ["-source_indexed_at", "-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["source_uri"],
                name="unique_bluesky_post_map_source_uri",
            )
        ]


class BlueskySyncRun(BaseModel):
    source_settings = models.ForeignKey(
        "bluesky.BlueskySourceSettings",
        on_delete=models.CASCADE,
        related_name="sync_runs",
    )
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField()
    imported_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    removed_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = "bluesky"
        ordering = ["-completed_at", "-created_at"]
        indexes = [
            models.Index(
                fields=["source_settings", "-completed_at", "-created_at"],
                name="bluesky_sr_src_comp_idx",
            )
        ]
