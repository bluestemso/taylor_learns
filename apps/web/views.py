from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from health_check.views import MainView

from apps.content.models import BlogIndexPage

from .gadgets import get_gadgets_url


def home(request):
    # Get the blog index page to use as home page
    blog_index = BlogIndexPage.objects.live().first()

    if not blog_index:
        # Fallback if no blog index exists
        return render(
            request,
            "web/home.html",
            context={
                "blog_posts": [],
                "site_name": settings.PROJECT_METADATA.get("NAME", "Taylor Learns"),
                "page_title": _("Home"),
            },
        )

    return render(
        request,
        "content/blog_index_page.html",
        context={
            "page": blog_index,
            "page_title": blog_index.title,
        },
    )


def simulate_error(request):
    raise Exception("This is a simulated error.")


def gadgets_bridge(request):
    gadgets_url = get_gadgets_url(request)
    if not gadgets_url:
        raise Http404
    return HttpResponseRedirect(f"{gadgets_url}/")


class HealthCheck(MainView):
    def get(self, request, *args, **kwargs):
        tokens = settings.HEALTH_CHECK_TOKENS
        if tokens and request.GET.get("token") not in tokens:
            raise Http404
        return super().get(request, *args, **kwargs)
