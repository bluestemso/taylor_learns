#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

from apps.web.template_checks import (
    find_invalid_responsive_custom_classes_by_line,
    normalize_template_paths,
)


def _default_template_files(repo_root: Path) -> list[Path]:
    html_files: list[Path] = []
    for root in (repo_root / "templates", repo_root / "apps"):
        if root.exists():
            html_files.extend(root.rglob("*.html"))
    return sorted(set(html_files))


def _provided_template_files(repo_root: Path, args: list[str]) -> list[Path]:
    normalized = normalize_template_paths(args)
    files: list[Path] = []
    for raw_path in normalized:
        path = Path(raw_path)
        full_path = path if path.is_absolute() else repo_root / path
        if full_path.exists() and full_path.is_file():
            files.append(full_path)
    return sorted(set(files))


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    targets = _provided_template_files(repo_root, sys.argv[1:]) or _default_template_files(repo_root)

    violations: list[str] = []
    for target in targets:
        relative_path = target.relative_to(repo_root)
        template_content = target.read_text(encoding="utf-8")
        for line_number, matches in find_invalid_responsive_custom_classes_by_line(template_content):
            joined = ", ".join(matches)
            violations.append(f"{relative_path}:{line_number} -> {joined}")

    if violations:
        print("Found invalid responsive custom class variants:")
        for violation in violations:
            print(f"- {violation}")
        print("Use responsive standard border/spacing utilities instead of patterns like 'md:ei-*'.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
