import json
import shutil
import tarfile
import tempfile
import uuid
from pathlib import Path

import httpx
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify

from .models import GadgetSource, GadgetSyncStatus

REQUIRED_GADGET_FILES = ("index.html", "gadget.json")


def sync_all_gadgets(
    *,
    dry_run: bool = False,
    force: bool = False,
    slug: str | None = None,
    repo_full_name: str | None = None,
    topics: list[str] | None = None,
    owners: list[str] | None = None,
) -> dict[str, int]:
    summary = {
        "discovered": 0,
        "created": 0,
        "updated": 0,
        "synced": 0,
        "skipped": 0,
        "failed": 0,
    }

    if slug:
        sources = list(GadgetSource.objects.filter(slug=slug))
    elif repo_full_name:
        source = GadgetSource.objects.filter(repo_full_name=repo_full_name).first()
        if source is None:
            repository = fetch_repository(repo_full_name)
            source, created, updated = upsert_source(repository)
            summary["created"] += int(created)
            summary["updated"] += int(updated)
        sources = [source]
    else:
        repositories = discover_repositories(topics=topics, owners=owners)
        summary["discovered"] = len(repositories)
        sources = []
        for repository in repositories:
            source, created, updated = upsert_source(repository)
            summary["created"] += int(created)
            summary["updated"] += int(updated)
            sources.append(source)

    for source in sources:
        result = sync_gadget_source(source=source, dry_run=dry_run, force=force)
        status = result.get("status")
        if status == "success":
            summary["synced"] += 1
        elif status == "skipped":
            summary["skipped"] += 1
        else:
            summary["failed"] += 1

    return summary


def discover_repositories(topics: list[str] | None = None, owners: list[str] | None = None) -> list[dict]:
    discovered_topics = topics or list(getattr(settings, "GADGETS_SYNC_TOPICS", []))
    allowed_owners = {owner.lower() for owner in (owners or list(getattr(settings, "GADGETS_SYNC_OWNERS", [])))}
    repositories: dict[str, dict] = {}

    with github_client() as client:
        for topic in discovered_topics:
            if not topic:
                continue

            page = 1
            while True:
                response = client.get(
                    "/search/repositories",
                    params={
                        "q": f"topic:{topic} archived:false",
                        "sort": "updated",
                        "order": "desc",
                        "per_page": 100,
                        "page": page,
                    },
                )
                response.raise_for_status()
                payload = response.json()
                items = payload.get("items", [])

                for item in items:
                    owner_login = str(item.get("owner", {}).get("login", "")).lower()
                    if allowed_owners and owner_login not in allowed_owners:
                        continue

                    full_name = str(item.get("full_name", "")).strip()
                    if not full_name:
                        continue

                    repositories[full_name] = {
                        "full_name": full_name,
                        "name": item.get("name", ""),
                        "default_branch": item.get("default_branch", "main"),
                    }

                if len(items) < 100:
                    break
                page += 1

    return sorted(repositories.values(), key=lambda repo: repo["full_name"])


def fetch_repository(repo_full_name: str) -> dict:
    with github_client() as client:
        response = client.get(f"/repos/{repo_full_name}")
        response.raise_for_status()
        payload = response.json()
        return {
            "full_name": payload.get("full_name", repo_full_name),
            "name": payload.get("name", ""),
            "default_branch": payload.get("default_branch", "main"),
        }


def upsert_source(repository: dict) -> tuple[GadgetSource, bool, bool]:
    full_name = str(repository.get("full_name", "")).strip()
    if not full_name:
        raise ValueError("Repository payload missing full_name")

    name = str(repository.get("name", "")).strip() or full_name.rsplit("/", maxsplit=1)[-1]
    default_branch = str(repository.get("default_branch", "main")).strip() or "main"

    source = GadgetSource.objects.filter(repo_full_name=full_name).first()
    if source is None:
        source = GadgetSource.objects.create(
            slug=next_available_slug(slugify(name) or name.lower()),
            repo_full_name=full_name,
            default_branch=default_branch,
        )
        return source, True, False

    updated = False
    if source.default_branch != default_branch:
        source.default_branch = default_branch
        updated = True

    if updated:
        source.save(update_fields=["default_branch", "updated_at"])

    return source, False, updated


def sync_gadget_source(source: GadgetSource, dry_run: bool = False, force: bool = False) -> dict[str, str]:
    try:
        with github_client() as client:
            repo_response = client.get(f"/repos/{source.repo_full_name}")
            repo_response.raise_for_status()
            repo_payload = repo_response.json()

            default_branch = str(repo_payload.get("default_branch", "")).strip() or source.default_branch or "main"
            if source.default_branch != default_branch:
                source.default_branch = default_branch
                source.save(update_fields=["default_branch", "updated_at"])

            commit = fetch_latest_commit(client=client, repo_full_name=source.repo_full_name, branch=default_branch)
            sha = str(commit.get("sha", ""))
            if not sha:
                raise ValueError(f"Could not determine commit SHA for {source.repo_full_name}")

            if not force and source.last_synced_sha == sha:
                source.last_sync_status = GadgetSyncStatus.SKIPPED
                source.last_sync_error = ""
                source.save(update_fields=["last_sync_status", "last_sync_error", "updated_at"])
                return {"status": "skipped", "sha": sha}

            if dry_run:
                return {"status": "success", "sha": sha}

            archive_response = client.get(
                f"/repos/{source.repo_full_name}/tarball/{sha}",
                follow_redirects=True,
            )
            archive_response.raise_for_status()

            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                archive_path = tmp_path / "repository.tar.gz"
                archive_path.write_bytes(archive_response.content)

                extraction_path = tmp_path / "extracted"
                extraction_path.mkdir(parents=True, exist_ok=True)

                safe_extract_tarball(archive_path=archive_path, destination=extraction_path)
                repo_root = resolve_repo_root(extraction_path)

                validate_gadget_repo(repo_root)
                metadata = parse_gadget_metadata(repo_root / "gadget.json")
                publish_gadget(repo_root=repo_root, slug=source.slug)

            source.title = metadata["title"]
            source.description = metadata["description"]
            source.tags = metadata["tags"]
            source.published = metadata["published"]
            source.last_synced_sha = sha
            source.commit_url = str(commit.get("html_url", ""))
            source.last_synced_at = timezone.now()
            source.last_sync_status = GadgetSyncStatus.SUCCESS
            source.last_sync_error = ""
            source.save()
            return {"status": "success", "sha": sha}
    except Exception as exc:  # noqa: BLE001
        source.last_sync_status = GadgetSyncStatus.ERROR
        source.last_sync_error = str(exc)
        source.save(update_fields=["last_sync_status", "last_sync_error", "updated_at"])
        return {"status": "error", "error": str(exc)}


def fetch_latest_commit(client: httpx.Client, repo_full_name: str, branch: str) -> dict:
    response = client.get(f"/repos/{repo_full_name}/commits/{branch}")
    response.raise_for_status()
    payload = response.json()
    return {
        "sha": payload.get("sha", ""),
        "html_url": payload.get("html_url", ""),
    }


def parse_gadget_metadata(metadata_path: Path) -> dict:
    payload = json.loads(metadata_path.read_text())
    if not isinstance(payload, dict):
        raise ValueError("gadget.json must contain an object")

    title = payload.get("title")
    description = payload.get("description")
    status = payload.get("status")
    tags = payload.get("tags")

    parsed_tags = []
    if isinstance(tags, list):
        parsed_tags = [str(tag).strip().lower() for tag in tags if str(tag).strip()]

    return {
        "title": str(title).strip() if isinstance(title, str) else "",
        "description": str(description).strip() if isinstance(description, str) else "",
        "tags": parsed_tags,
        "published": str(status).strip().lower() == "published",
    }


def validate_gadget_repo(repo_root: Path):
    missing_files = [file_name for file_name in REQUIRED_GADGET_FILES if not (repo_root / file_name).is_file()]
    if missing_files:
        missing = ", ".join(missing_files)
        raise ValueError(f"Missing required gadget files: {missing}")


def publish_gadget(repo_root: Path, slug: str):
    gadgets_root = Path(settings.BASE_DIR) / "gadgets"
    gadgets_root.mkdir(parents=True, exist_ok=True)

    destination = gadgets_root / slug
    staging = gadgets_root / f".{slug}.staging-{uuid.uuid4().hex}"
    backup = gadgets_root / f".{slug}.backup-{uuid.uuid4().hex}"

    shutil.copytree(repo_root, staging, ignore=shutil.ignore_patterns(".git", ".github", "__pycache__"))
    validate_gadget_repo(staging)

    try:
        if destination.exists():
            destination.replace(backup)
        staging.replace(destination)
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:  # noqa: BLE001
        if destination.exists():
            shutil.rmtree(destination)
        if backup.exists() and not destination.exists():
            backup.replace(destination)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def safe_extract_tarball(archive_path: Path, destination: Path):
    with tarfile.open(archive_path, "r:*") as tar:
        resolved_destination = destination.resolve()
        for member in tar.getmembers():
            target = (destination / member.name).resolve()
            if not target.is_relative_to(resolved_destination):
                raise ValueError("Archive contains invalid paths")

        tar.extractall(path=destination, filter="data")


def resolve_repo_root(extraction_path: Path) -> Path:
    entries = [entry for entry in extraction_path.iterdir()]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return extraction_path


def next_available_slug(base_slug: str) -> str:
    if not base_slug:
        base_slug = f"gadget-{uuid.uuid4().hex[:8]}"

    candidate = base_slug
    suffix = 2
    while GadgetSource.objects.filter(slug=candidate).exists():
        candidate = f"{base_slug}-{suffix}"
        suffix += 1
    return candidate


def github_client() -> httpx.Client:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "taylor-learns-gadgets-sync",
    }
    token = str(getattr(settings, "GADGETS_GITHUB_TOKEN", "")).strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    return httpx.Client(
        base_url="https://api.github.com",
        headers=headers,
        timeout=30,
    )
