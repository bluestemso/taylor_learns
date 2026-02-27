import json
import mimetypes
from pathlib import Path

from django.conf import settings
from django.db import OperationalError, ProgrammingError
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, HttpResponseBase
from django.shortcuts import render

try:
    from django.test.testcases import DatabaseOperationForbidden
except Exception:  # pragma: no cover
    DatabaseOperationForbidden = RuntimeError

from .models import GadgetSource

GADGETS_ROOT = settings.BASE_DIR / "gadgets"


def index(request: HttpRequest) -> HttpResponse:
    main_site_url = str(settings.PROJECT_METADATA.get("URL", "")).rstrip("/")
    context = {
        "gadgets": _list_gadgets(),
        "main_site_url": main_site_url,
        "blog_url": f"{main_site_url}/" if main_site_url else "/",
        "portfolio_url": f"{main_site_url}/portfolio/" if main_site_url else "/portfolio/",
    }
    return render(request, "gadgets/index.html", context)


def detail(request: HttpRequest, slug: str) -> HttpResponseBase:
    if _is_blocked(slug):
        return HttpResponse(status=404)

    try:
        gadget_dir = _get_gadget_dir(slug)
        index_file = _safe_path(gadget_dir, "index.html")
        if not index_file.is_file():
            return HttpResponse(status=404)
        return FileResponse(index_file.open("rb"), content_type="text/html; charset=utf-8")
    except Http404:
        return HttpResponse(status=404)


def asset(request: HttpRequest, slug: str, asset_path: str) -> HttpResponseBase:
    if _is_blocked(slug):
        return HttpResponse(status=404)

    try:
        gadget_dir = _get_gadget_dir(slug)
        file_path = _safe_path(gadget_dir, asset_path)
        if not file_path.is_file():
            return HttpResponse(status=404)
    except Http404:
        return HttpResponse(status=404)

    content_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(file_path.open("rb"), content_type=content_type or "application/octet-stream")


def _list_gadgets() -> list[dict[str, str]]:
    if not GADGETS_ROOT.is_dir():
        return []

    source_by_slug = _source_map_by_slug()
    gadgets = []
    for gadget_dir in sorted(path for path in GADGETS_ROOT.iterdir() if path.is_dir()):
        index_file = gadget_dir / "index.html"
        if not index_file.is_file():
            continue

        slug = gadget_dir.name
        source = source_by_slug.get(slug)
        if source and source.is_blocked:
            continue

        metadata = _read_metadata(gadget_dir)
        if source and source.is_hidden:
            continue

        if not _is_published(metadata, source):
            continue

        gadgets.append(
            {
                "slug": slug,
                "title": (source.title if source and source.title else metadata.get("title"))
                or slug.replace("-", " ").title(),
                "description": (source.description if source and source.description else metadata.get("description"))
                or "",
                "is_featured": source.is_featured if source else False,
                "display_order": source.display_order if source else 1000,
            }
        )

    gadgets.sort(
        key=lambda gadget: (not bool(gadget["is_featured"]), int(gadget["display_order"]), str(gadget["title"]))
    )
    return [{"slug": g["slug"], "title": g["title"], "description": g["description"]} for g in gadgets]


def _read_metadata(gadget_dir: Path) -> dict:
    metadata_file = gadget_dir / "gadget.json"
    if not metadata_file.is_file():
        return {}

    try:
        payload = json.loads(metadata_file.read_text())
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(payload, dict):
        return {}

    metadata: dict[str, str | list[str]] = {}
    for key in ("title", "description", "status"):
        value = payload.get(key)
        if isinstance(value, str):
            metadata[key] = value

    tags = payload.get("tags")
    if isinstance(tags, list):
        metadata["tags"] = [str(tag).strip().lower() for tag in tags if str(tag).strip()]

    return metadata


def _is_published(metadata: dict, source: GadgetSource | None) -> bool:
    if source and source.published:
        return True

    status = metadata.get("status")
    if isinstance(status, str):
        return status.strip().lower() == "published"
    return False


def _source_map_by_slug() -> dict[str, GadgetSource]:
    try:
        return {source.slug: source for source in GadgetSource.objects.all()}
    except (OperationalError, ProgrammingError, DatabaseOperationForbidden):
        return {}


def _is_blocked(slug: str) -> bool:
    try:
        return GadgetSource.objects.filter(slug=slug, is_blocked=True).exists()
    except (OperationalError, ProgrammingError, DatabaseOperationForbidden):
        return False


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
