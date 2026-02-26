from urllib.parse import urlsplit

from django.conf import settings


class SubdomainURLRoutingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        configured_hosts = getattr(settings, "GADGETS_HOSTS", [])
        self.gadgets_hosts = set()
        for host in configured_hosts:
            normalized = self._normalize_host(host)
            if normalized:
                self.gadgets_hosts.add(normalized)

    def __call__(self, request):
        host = request.get_host().split(":", 1)[0].lower()
        if host in self.gadgets_hosts:
            request.urlconf = "apps.gadgets.urls"
        return self.get_response(request)

    @staticmethod
    def _normalize_host(value: str) -> str:
        if not value:
            return ""

        parsed = urlsplit(value if "://" in value else f"//{value}")
        if parsed.hostname:
            return parsed.hostname.lower()
        return ""
