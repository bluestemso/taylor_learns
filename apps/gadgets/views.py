import json
import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, HttpResponseBase
from django.template.loader import render_to_string

GADGETS_ROOT = settings.BASE_DIR / "gadgets"


def index(request: HttpRequest) -> HttpResponse:
    html = render_to_string("gadgets/index.html", {"gadgets": _list_gadgets()})
    return HttpResponse(html)


def detail(request: HttpRequest, slug: str) -> HttpResponseBase:
    gadget_dir = _get_gadget_dir(slug)
    index_file = _safe_path(gadget_dir, "index.html")
    if not index_file.is_file():
        raise Http404
    return FileResponse(index_file.open("rb"), content_type="text/html; charset=utf-8")


def asset(request: HttpRequest, slug: str, asset_path: str) -> HttpResponseBase:
    gadget_dir = _get_gadget_dir(slug)
    file_path = _safe_path(gadget_dir, asset_path)
    if not file_path.is_file():
        raise Http404

    content_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(file_path.open("rb"), content_type=content_type or "application/octet-stream")


def _list_gadgets() -> list[dict[str, str]]:
    if not GADGETS_ROOT.is_dir():
        return []

    gadgets = []
    for gadget_dir in sorted(path for path in GADGETS_ROOT.iterdir() if path.is_dir()):
        index_file = gadget_dir / "index.html"
        if not index_file.is_file():
            continue

        metadata = _read_metadata(gadget_dir)
        slug = gadget_dir.name
        gadgets.append(
            {
                "slug": slug,
                "title": metadata.get("title") or slug.replace("-", " ").title(),
                "description": metadata.get("description") or "",
            }
        )

    return gadgets


def _read_metadata(gadget_dir: Path) -> dict[str, str]:
    metadata_file = gadget_dir / "gadget.json"
    if not metadata_file.is_file():
        return {}

    try:
        payload = json.loads(metadata_file.read_text())
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(payload, dict):
        return {}

    metadata: dict[str, str] = {}
    for key in ("title", "description"):
        value = payload.get(key)
        if isinstance(value, str):
            metadata[key] = value
    return metadata


def _get_gadget_dir(slug: str) -> Path:
    gadget_dir = _safe_path(GADGETS_ROOT, slug)
    if not gadget_dir.is_dir():
        raise Http404
    return gadget_dir


def _safe_path(base: Path, relative_path: str) -> Path:
    resolved_base = base.resolve()
    resolved_target = (resolved_base / relative_path).resolve()
    if not resolved_target.is_relative_to(resolved_base):
        raise Http404
    return resolved_target
