from datetime import date

from django.test import TestCase
from wagtail.models import Page

from apps.content.models import BlogIndexPage, BlogPage, ContentPage


class TestBlogIndexOrdering(TestCase):
    def test_blog_index_orders_by_content_date_not_publish_timestamp(self):
        root = Page.get_first_root_node()
        blog_index = BlogIndexPage(title="Blog", slug="blog")
        root.add_child(instance=blog_index)
        blog_index.save_revision().publish()

        newer_post = BlogPage(title="Newer", slug="newer", date=date(2024, 1, 2), body=[])
        blog_index.add_child(instance=newer_post)
        newer_post.save_revision().publish()

        older_post = BlogPage(title="Older", slug="older", date=date(2024, 1, 1), body=[])
        blog_index.add_child(instance=older_post)
        older_post.save_revision().publish()

        ordered_posts = list(blog_index.get_ordered_blog_posts())

        self.assertEqual([post.slug for post in ordered_posts[:2]], ["newer", "older"])

    def test_blog_index_handles_pages_without_date_using_deterministic_fallback(self):
        root = Page.get_first_root_node()
        blog_index = BlogIndexPage(title="Blog", slug="blog")
        root.add_child(instance=blog_index)
        blog_index.save_revision().publish()

        dated_post = BlogPage(title="Dated", slug="dated", date=date(2100, 1, 1), body=[])
        blog_index.add_child(instance=dated_post)
        dated_post.save_revision().publish()

        no_date_post = ContentPage(title="Legacy", slug="legacy", body=[])
        blog_index.add_child(instance=no_date_post)
        no_date_post.save_revision().publish()

        older_post = BlogPage(title="Older", slug="older", date=date(2000, 1, 1), body=[])
        blog_index.add_child(instance=older_post)
        older_post.save_revision().publish()

        ordered_posts = list(blog_index.get_ordered_blog_posts())

        self.assertEqual([post.slug for post in ordered_posts[:3]], ["dated", "legacy", "older"])
