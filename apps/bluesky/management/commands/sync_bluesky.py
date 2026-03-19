from django.core.management.base import BaseCommand

from apps.bluesky.sync import run_sync


class Command(BaseCommand):
    help = "Sync Bluesky posts into microblog entries."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        result = run_sync(limit=int(options.get("limit") or 100))
        self.stdout.write(
            self.style.SUCCESS(
                f"Sync complete: imported={result['imported']} "
                f"updated={result['updated']} "
                f"skipped={result['skipped']} "
                f"failed={result['failed']}"
            )
        )
