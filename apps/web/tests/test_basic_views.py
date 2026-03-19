from django.conf import settings
from django.templatetags.static import static
from django.test import TestCase, override_settings
from django.urls import resolve, reverse


class TestBasicViews(TestCase):
    def test_landing_page(self):
        self._assert_200(reverse("web:home"))

    def test_signup(self):
        self._assert_200(reverse("account_signup"))

    def test_login(self):
        self._assert_200(reverse("account_login"))

    def test_terms(self):
        self._assert_200(reverse("web:terms"))

    def test_public_profile_page(self):
        response = self.client.get("/profile/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Taylor Schaack - an operator turned software builder.")
        self.assertContains(response, static("images/web/taylor-profile-art.png"))
        self.assertContains(response, 'alt="Taylor Schaack profile illustration"')

    def test_public_profile_page_is_served_by_wagtail(self):
        match = resolve("/profile/")

        self.assertEqual(match.url_name, "wagtail_serve")

    def test_robots(self):
        self._assert_200(reverse("web:robots.txt"))

    def test_simulate_error_route_is_not_public(self):
        self.client.raise_request_exception = False
        with self.assertLogs("django.request", level="WARNING"):
            response = self.client.get("/simulate_error/")
        self.assertEqual(response.status_code, 404)

    def test_top_nav_includes_gadgets_link(self):
        response = self.client.get(reverse("web:home"))
        gadgets_host = settings.GADGETS_HOSTS[0]
        expected_url = gadgets_host if gadgets_host.startswith(("http://", "https://")) else f"http://{gadgets_host}"

        self.assertContains(response, f'href="{expected_url}"')
        self.assertContains(response, "Gadgets")

    def test_gadgets_bridge_redirects_to_gadgets_subdomain(self):
        response = self.client.get(reverse("web:gadgets"))
        gadgets_host = settings.GADGETS_HOSTS[0]
        expected_url = gadgets_host if gadgets_host.startswith(("http://", "https://")) else f"http://{gadgets_host}"
        self.assertRedirects(response, f"{expected_url}/", fetch_redirect_response=False)

    def test_gadgets_bridge_preserves_non_default_port(self):
        response = self.client.get(reverse("web:gadgets"), HTTP_HOST="localhost:8000")
        self.assertRedirects(response, "http://gadgets.localhost:8000/", fetch_redirect_response=False)

    def test_top_nav_does_not_mark_gadgets_active_on_main_site(self):
        response = self.client.get(reverse("web:home"), HTTP_HOST="localhost:8000")
        self.assertFalse(response.context["gadgets_is_active"])
        self.assertNotContains(response, '<a class="tab tab-active" href="http://gadgets.localhost:8000">')

    @override_settings(GADGETS_HOSTS=["gadgets.taylorlearns.com"])
    def test_top_nav_gadgets_link_does_not_reuse_internal_app_port(self):
        response = self.client.get(reverse("web:home"), HTTP_HOST="taylorlearns.com:8000", secure=True)
        self.assertContains(response, 'href="https://gadgets.taylorlearns.com"')
        self.assertNotContains(response, 'href="https://gadgets.taylorlearns.com:8000"')

    def _assert_200(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
