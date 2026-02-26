import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings


class TestCreateGadgetCommand(SimpleTestCase):
    def test_creates_scaffold_with_agent_instructions(self):
        with TemporaryDirectory() as tmpdir, override_settings(BASE_DIR=Path(tmpdir)):
            call_command("create_gadget", "focus-timer", title="Focus Timer")

            gadget_dir = Path(tmpdir) / "gadgets" / "focus-timer"
            self.assertTrue((gadget_dir / "index.html").is_file())
            self.assertTrue((gadget_dir / "styles.css").is_file())
            self.assertTrue((gadget_dir / "app.js").is_file())
            self.assertTrue((gadget_dir / "gadget.json").is_file())
            self.assertTrue((gadget_dir / "AGENT.md").is_file())

            metadata = json.loads((gadget_dir / "gadget.json").read_text())
            self.assertEqual(metadata["title"], "Focus Timer")
            self.assertIn("description", metadata)
            self.assertIn("status", metadata)
            self.assertIn("tags", metadata)

            instructions = (gadget_dir / "AGENT.md").read_text()
            self.assertIn("gadget.json", instructions)
            self.assertIn("self-contained", instructions)

    def test_fails_when_gadget_already_exists(self):
        with TemporaryDirectory() as tmpdir, override_settings(BASE_DIR=Path(tmpdir)):
            call_command("create_gadget", "focus-timer", title="Focus Timer")

            with self.assertRaises(CommandError):
                call_command("create_gadget", "focus-timer", title="Focus Timer")
