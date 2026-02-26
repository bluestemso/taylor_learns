# Instructions For Coding Agents

1. Keep this gadget self-contained in this folder (`gadgets/tmux-dojo/`).
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
