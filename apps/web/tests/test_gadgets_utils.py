from django.test import RequestFactory, SimpleTestCase, override_settings

from apps.web.gadgets import get_gadgets_url, is_gadgets_request


class TestGadgetsUtils(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(GADGETS_HOSTS=["gadgets.localhost"])
    def test_get_gadgets_url_preserves_port_for_localhost_dev(self):
        request = self.factory.get("/", HTTP_HOST="localhost:8000")

        self.assertEqual(get_gadgets_url(request), "http://gadgets.localhost:8000")

    @override_settings(GADGETS_HOSTS=["gadgets.taylorlearns.com"])
    def test_get_gadgets_url_does_not_preserve_internal_port_for_non_local_hosts(self):
        request = self.factory.get("/", secure=True, HTTP_HOST="taylorlearns.com:8000")

        self.assertEqual(get_gadgets_url(request), "https://gadgets.taylorlearns.com")

    @override_settings(GADGETS_HOSTS=["gadgets.taylorlearns.com"])
    def test_is_gadgets_request_matches_exact_host(self):
        main_request = self.factory.get("/", HTTP_HOST="taylorlearns.com")
        self.assertFalse(is_gadgets_request(main_request))

        gadgets_request = self.factory.get("/", HTTP_HOST="gadgets.taylorlearns.com")
        self.assertTrue(is_gadgets_request(gadgets_request))
