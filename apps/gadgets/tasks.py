from celery import shared_task
from django.conf import settings

from .sync import sync_all_gadgets


@shared_task
def sync_gadgets_task():
    if not settings.GADGETS_SYNC_ENABLED:
        return {"status": "disabled"}

    return sync_all_gadgets()
