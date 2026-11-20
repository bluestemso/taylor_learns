#!/usr/bin/env python3
"""Check all pinned public npm or PyPI artifacts against their registry and release age."""

import argparse
import concurrent.futures
import datetime
import json
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request

AGE_SECONDS = 72 * 3600


def metadata(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "vps-release-age/1"})
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except (TimeoutError, OSError) as error:
            if (
                attempt == 2
                or isinstance(error, urllib.error.HTTPError)
                and error.code not in (429, 500, 502, 503, 504)
            ):
                raise
            time.sleep(2**attempt)


def npm_entries(lock, local_packages):
    if lock.get("lockfileVersion") not in (2, 3) or not lock.get("packages"):
        raise ValueError("A complete npm v2/v3 lockfile is required")
    for path, entry in lock["packages"].items():
        if path == "":
            continue
        if path in local_packages:
            if set(entry) - {"name", "version", "license", "dependencies", "devDependencies", "engines"}:
                raise ValueError(f"Review local package metadata: {path}")
            continue
        if (
            entry.get("link")
            and entry.get("resolved") in local_packages
            and path == "node_modules/" + entry["resolved"]
        ):
            continue
        if entry.get("inBundle") and not entry.get("resolved") and "/node_modules/" in path:
            parent, child = path.rsplit("/node_modules/", 1)
            parent_record = lock["packages"].get(parent, {})
            if child in parent_record.get("bundleDependencies", []) and parent_record.get("integrity", "").startswith(
                "sha512-"
            ):
                # npm extracts bundled files from this separately age- and integrity-checked parent tarball.
                continue
        if not path.startswith("node_modules/") or entry.get("link"):
            raise ValueError(f"Review non-registry or workspace entry at {path}")
        name = entry.get("name", path.rsplit("node_modules/", 1)[-1])
        resolved = entry.get("resolved", "")
        if urllib.parse.urlparse(resolved).netloc != "registry.npmjs.org" or not resolved.startswith("https://"):
            raise ValueError(f"Review external npm source for {name}")
        integrity = entry.get("integrity", "")
        if not re.fullmatch(r"sha512-[A-Za-z0-9+/]+={0,2}", integrity):
            raise ValueError(f"Missing SHA-512 integrity for {name}")
        yield ("npm", name, entry["version"], resolved, integrity)


def python_entries(lock):
    for entry in lock["package"]:
        source = entry["source"]
        if source in ({"editable": "."}, {"virtual": "."}):
            continue
        if source != {"registry": "https://pypi.org/simple"}:
            raise ValueError(f"Review non-PyPI source for {entry['name']}")
        artifacts = list(entry.get("wheels", []))
        if entry.get("sdist"):
            artifacts.append(entry["sdist"])
        if not artifacts:
            raise ValueError(f"Missing locked artifacts for {entry['name']}")
        for artifact in artifacts:
            digest = artifact["hash"]
            if not re.fullmatch("sha256:[0-9a-f]{64}", digest):
                raise ValueError(f"Missing artifact digest for {entry['name']}")
            yield ("pypi", entry["name"], entry["version"], artifact["url"], digest)


def check_group(item, now):
    (ecosystem, name), artifacts = item
    escaped = urllib.parse.quote(name, safe="")
    info = metadata("https://registry.npmjs.org/" + escaped) if ecosystem == "npm" else {}
    for _, _, version, url, digest in artifacts:
        if ecosystem == "npm":
            release = info["versions"][version]
            if release["dist"]["tarball"] != url or release["dist"]["integrity"] != digest:
                raise ValueError(f"{name} {version}: npm artifact mismatch")
            stamp = info["time"][version]
        else:
            if version not in info:
                release_url = f"https://pypi.org/pypi/{escaped}/{urllib.parse.quote(version, safe='')}/json"
                info[version] = {item["url"]: item for item in metadata(release_url)["urls"]}
            release = info[version].get(url)
            if not release or release["yanked"] or "sha256:" + release["digests"]["sha256"] != digest:
                raise ValueError(f"{name} {version}: yanked or mismatched Python artifact")
            stamp = release["upload_time_iso_8601"]
        published = datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()
        if now - published < AGE_SECONDS:
            raise ValueError(f"{name} {version}: hold until 72 hours after {stamp}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--local-package",
        action="append",
        default=[],
        choices=["api-client"],
        help="Allow this project-owned local npm package",
    )
    parser.add_argument("locks", type=pathlib.Path, nargs="+")
    args = parser.parse_args()
    groups = {}
    for path in args.locks:
        if path.name == "uv.lock":
            import tomllib

            with path.open("rb") as stream:
                entries = python_entries(tomllib.load(stream))
                for item in entries:
                    groups.setdefault(item[:2], set()).add(item)
        elif path.name == "package-lock.json":
            for item in npm_entries(json.loads(path.read_text()), args.local_package):
                groups.setdefault(item[:2], set()).add(item)
        else:
            raise ValueError(f"Unknown lockfile type: {path.name}")
    now = time.time()
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        jobs = {pool.submit(check_group, item, now): item[0] for item in groups.items()}
        for job in concurrent.futures.as_completed(jobs):
            try:
                job.result()
            except Exception as error:
                failures.append(f"{jobs[job]}: {error}")
    if failures:
        raise SystemExit("\n".join(sorted(failures)))
    print(f"Passed registry integrity and 72-hour age for {len(groups)} package names.")


if __name__ == "__main__":
    main()
