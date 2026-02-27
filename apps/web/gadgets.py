from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpRequest


def _configured_gadget_hosts() -> list[str]:
    configured_hosts = getattr(settings, "GADGETS_HOSTS", [])
    return [host for host in configured_hosts if isinstance(host, str)]


def _hostname_and_port(host_or_url: str) -> tuple[str, int | None]:
    normalized = host_or_url.strip().rstrip("/")
    if not normalized:
        return "", None

    parsed = urlsplit(normalized if normalized.startswith(("http://", "https://")) else f"//{normalized}")
    if not parsed.hostname:
        return "", None

    return parsed.hostname.lower(), parsed.port


def _is_local_dev_hostname(hostname: str) -> bool:
    return hostname == "localhost" or hostname == "127.0.0.1" or hostname.endswith(".localhost")


def _request_port(request: HttpRequest, scheme: str) -> str:
    request_host = request.get_host()
    parsed_host = urlsplit(f"//{request_host}")
    port = str(parsed_host.port) if parsed_host.port is not None else request.get_port()

    if (scheme == "http" and port == "80") or (scheme == "https" and port == "443"):
        return ""
    return port


def is_gadgets_request(request: HttpRequest) -> bool:
    request_host, request_port = _hostname_and_port(request.get_host())
    if not request_host:
        return False

    for configured_host in _configured_gadget_hosts():
        configured_hostname, configured_port = _hostname_and_port(configured_host)
        if not configured_hostname:
            continue

        if request_host != configured_hostname:
            continue

        if configured_port is not None and request_port is not None and request_port != configured_port:
            continue

        return True

    return False


def get_gadgets_url(request: HttpRequest) -> str:
    for host in _configured_gadget_hosts():
        normalized_host = host.strip().rstrip("/")
        if not normalized_host:
            continue

        if normalized_host.startswith(("http://", "https://")):
            parsed = urlsplit(normalized_host)
            if not parsed.hostname:
                continue

            if parsed.port is not None:
                return normalized_host

            if not _is_local_dev_hostname(parsed.hostname):
                return normalized_host

            request_port = _request_port(request, parsed.scheme)
            if not request_port:
                return normalized_host
            return f"{parsed.scheme}://{parsed.hostname}:{request_port}"

        parsed = urlsplit(f"//{normalized_host}")
        if not parsed.hostname:
            continue

        if parsed.port is not None:
            return f"{request.scheme}://{parsed.netloc}"

        if not _is_local_dev_hostname(parsed.hostname):
            return f"{request.scheme}://{parsed.hostname}"

        request_port = _request_port(request, request.scheme)
        if request_port:
            return f"{request.scheme}://{parsed.hostname}:{request_port}"

        return f"{request.scheme}://{parsed.hostname}"

    return ""
