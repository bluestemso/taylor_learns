from django.test import SimpleTestCase

from apps.web.template_checks import find_invalid_responsive_custom_classes


class TestTemplateClassGuards(SimpleTestCase):
    def test_detects_invalid_responsive_ei_class_variants(self):
        bad_template = "<div class='md:ei-border-r xl:ei-border-l'></div>"

        matches = find_invalid_responsive_custom_classes(bad_template)

        self.assertEqual(matches, ["md:ei-border-r", "xl:ei-border-l"])

    def test_allows_standard_tailwind_responsive_classes(self):
        good_template = "<div class='md:border-r xl:border-l'></div>"

        matches = find_invalid_responsive_custom_classes(good_template)

        self.assertEqual(matches, [])
