from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpRequest


def _request_port(request: HttpRequest, scheme: str) -> str:
    request_host = request.get_host()
    parsed_host = urlsplit(f"//{request_host}")
    port = str(parsed_host.port) if parsed_host.port is not None else request.get_port()

    if (scheme == "http" and port == "80") or (scheme == "https" and port == "443"):
        return ""
    return port


def get_gadgets_url(request: HttpRequest) -> str:
    configured_hosts = getattr(settings, "GADGETS_HOSTS", [])
    for host in configured_hosts:
        if not isinstance(host, str):
            continue

        normalized_host = host.strip().rstrip("/")
        if not normalized_host:
            continue

        if normalized_host.startswith(("http://", "https://")):
            parsed = urlsplit(normalized_host)
            if not parsed.hostname:
                continue

            if parsed.port is not None:
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

        request_port = _request_port(request, request.scheme)
        if request_port:
            return f"{request.scheme}://{parsed.hostname}:{request_port}"

        return f"{request.scheme}://{parsed.hostname}"

    return ""
