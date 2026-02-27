from django.core.management.base import BaseCommand

from apps.gadgets.sync import sync_all_gadgets


class Command(BaseCommand):
    help = "Discover and sync gadgets from GitHub repositories."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--force", action="store_true")
        parser.add_argument("--slug", type=str, default="")
        parser.add_argument("--repo", type=str, default="")
        parser.add_argument("--topic", action="append", default=[])
        parser.add_argument("--owner", action="append", default=[])

    def handle(self, *args, **options):
        result = sync_all_gadgets(
            dry_run=bool(options["dry_run"]),
            force=bool(options["force"]),
            slug=str(options["slug"] or "").strip() or None,
            repo_full_name=str(options["repo"] or "").strip() or None,
            topics=list(options["topic"] or []),
            owners=list(options["owner"] or []),
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Sync complete: "
                f"discovered={result['discovered']} "
                f"created={result['created']} "
                f"updated={result['updated']} "
                f"synced={result['synced']} "
                f"skipped={result['skipped']} "
                f"failed={result['failed']}"
            )
        )
