from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from apps.bluesky.tasks import sync_bluesky_task


class TestSyncBlueskyTask(SimpleTestCase):
    @override_settings(BLUESKY_SYNC_ENABLED=False)
    @patch("apps.bluesky.tasks.run_sync")
    def test_task_returns_disabled_when_sync_is_disabled(self, mock_run_sync):
        result = sync_bluesky_task()

        self.assertEqual(result, {"status": "disabled"})
        mock_run_sync.assert_not_called()

    @override_settings(BLUESKY_SYNC_ENABLED=True)
    @patch("apps.bluesky.tasks.run_sync")
    def test_task_delegates_to_run_sync_when_enabled(self, mock_run_sync):
        mock_run_sync.return_value = {"imported": 1, "updated": 2, "removed": 3, "skipped": 4, "failed": 5}

        result = sync_bluesky_task()

        self.assertEqual(result, {"imported": 1, "updated": 2, "removed": 3, "skipped": 4, "failed": 5})
        mock_run_sync.assert_called_once_with(limit=100)
