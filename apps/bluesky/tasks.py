from celery import shared_task
from django.conf import settings

from apps.bluesky.sync import run_sync


@shared_task
def sync_bluesky_task():
    if not settings.BLUESKY_SYNC_ENABLED:
        return {"status": "disabled"}

    return run_sync(limit=100)
