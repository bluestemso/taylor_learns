from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase


class TestSyncGadgetsCommand(SimpleTestCase):
    @patch("apps.gadgets.management.commands.sync_gadgets.sync_all_gadgets")
    def test_sync_gadgets_forwards_options_to_service(self, mock_sync_all_gadgets):
        mock_sync_all_gadgets.return_value = {
            "discovered": 0,
            "created": 0,
            "updated": 0,
            "synced": 0,
            "skipped": 0,
            "failed": 0,
        }

        call_command(
            "sync_gadgets",
            "--dry-run",
            "--force",
            "--slug",
            "focus-timer",
            "--repo",
            "bluestemso/focus-timer",
            "--topic",
            "taylor-learns-gadget",
            "--topic",
            "browser-tool",
            "--owner",
            "bluestemso",
        )

        mock_sync_all_gadgets.assert_called_once_with(
            dry_run=True,
            force=True,
            slug="focus-timer",
            repo_full_name="bluestemso/focus-timer",
            topics=["taylor-learns-gadget", "browser-tool"],
            owners=["bluestemso"],
        )
