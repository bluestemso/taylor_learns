import json
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class Command(BaseCommand):
    help = "Create a self-contained gadget scaffold in gadgets/<slug>/"

    def add_arguments(self, parser):
        parser.add_argument("slug", type=str)
        parser.add_argument("--title", type=str, default="")
        parser.add_argument("--description", type=str, default="")

    def handle(self, *args, **options):
        slug = str(options["slug"]).strip().lower()
        if not SLUG_PATTERN.fullmatch(slug):
            raise CommandError("Slug must use lowercase letters, numbers, and single hyphens.")

        title = str(options["title"]).strip() or slug.replace("-", " ").title()
        description = (
            str(options["description"]).strip()
            or "One-sentence description for the gadgets index. Update this before publishing."
        )

        gadgets_root = Path(settings.BASE_DIR) / "gadgets"
        gadget_dir = gadgets_root / slug

        if gadget_dir.exists():
            raise CommandError(f"Gadget already exists: {gadget_dir}")

        gadget_dir.mkdir(parents=True, exist_ok=False)

        (gadget_dir / "index.html").write_text(self._index_template(title))
        (gadget_dir / "styles.css").write_text(self._styles_template())
        (gadget_dir / "app.js").write_text(self._app_template())

        metadata = {
            "title": title,
            "description": description,
            "status": "draft",
            "tags": [],
        }
        (gadget_dir / "gadget.json").write_text(json.dumps(metadata, indent=2) + "\n")
        (gadget_dir / "AGENT.md").write_text(self._agent_instructions())

        self.stdout.write(self.style.SUCCESS(f"Created gadget scaffold at {gadget_dir}"))

    def _index_template(self, title: str) -> str:
        return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>{title}</title>
    <link rel=\"stylesheet\" href=\"./styles.css\" />
  </head>
  <body>
    <main>
      <h1>{title}</h1>
      <p>Replace this with your gadget UI.</p>
    </main>
    <script type=\"module\" src=\"./app.js\"></script>
  </body>
</html>
"""

    def _styles_template(self) -> str:
        return """:root {
  --bg: #f4f7f4;
  --ink: #1e2c26;
  --surface: #ffffff;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: 'Space Grotesk', 'Avenir Next', 'Trebuchet MS', sans-serif;
  background: var(--bg);
  color: var(--ink);
  min-height: 100vh;
}

main {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1rem;
}
"""

    def _app_template(self) -> str:
        return """const root = document.querySelector('main');

if (root) {
  root.dataset.ready = 'true';
}
"""

    def _agent_instructions(self) -> str:
        return """# Instructions For Coding Agents

1. Keep this gadget self-contained in this folder (`gadgets/<slug>/`).
2. Use vanilla HTML/CSS/JS unless a dependency is explicitly requested.
3. Use relative asset paths in `index.html` (for example `./styles.css`, `./app.js`, `./assets/...`).
4. Do not use Django template tags in gadget files.
5. Before finishing, update `gadget.json` with:
   - `title`: human-readable title shown on the gadgets index.
   - `description`: one-sentence summary for the gadgets index card.
   - `status`: `draft` or `published`.
   - `tags`: short lowercase tags (for example `["terminal", "learning"]`).
6. Keep external network dependencies minimal; prefer local files in `assets/` when practical.
7. Ensure keyboard and mobile usability for interactive gadgets.
"""
