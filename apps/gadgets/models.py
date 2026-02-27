from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.utils.models import BaseModel


class GadgetSyncStatus(models.TextChoices):
    NEVER = "never", _("Never")
    SUCCESS = "success", _("Success")
    SKIPPED = "skipped", _("Skipped")
    ERROR = "error", _("Error")


class GadgetSource(BaseModel):
    slug = models.SlugField(unique=True)
    repo_full_name = models.CharField(max_length=255, unique=True)
    default_branch = models.CharField(max_length=255, default="main")

    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    published = models.BooleanField(default=False)

    is_hidden = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=1000)

    last_synced_sha = models.CharField(max_length=40, blank=True)
    last_synced_at = models.DateTimeField(blank=True, null=True)
    last_sync_status = models.CharField(
        max_length=20,
        choices=GadgetSyncStatus.choices,
        default=GadgetSyncStatus.NEVER,
    )
    last_sync_error = models.TextField(blank=True)
    commit_url = models.URLField(blank=True)

    class Meta:
        ordering = ["display_order", "slug"]

    def __str__(self):
        return self.slug
