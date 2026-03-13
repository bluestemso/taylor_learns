import re
from collections.abc import Iterable


RESPONSIVE_CUSTOM_CLASS_PATTERN = re.compile(r"\b(?:sm|md|lg|xl|2xl):ei-[a-z0-9-]+\b")


def find_invalid_responsive_custom_classes(template_content: str) -> list[str]:
    matches = RESPONSIVE_CUSTOM_CLASS_PATTERN.findall(template_content)
    return list(dict.fromkeys(matches))


def find_invalid_responsive_custom_classes_by_line(template_content: str) -> list[tuple[int, list[str]]]:
    violations: list[tuple[int, list[str]]] = []
    for line_number, line in enumerate(template_content.splitlines(), start=1):
        line_matches = find_invalid_responsive_custom_classes(line)
        if line_matches:
            violations.append((line_number, line_matches))
    return violations


def has_invalid_responsive_custom_classes(template_content: str) -> bool:
    return bool(RESPONSIVE_CUSTOM_CLASS_PATTERN.search(template_content))


def normalize_template_paths(paths: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(path for path in paths if path.endswith(".html")))
