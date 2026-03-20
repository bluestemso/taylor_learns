from datetime import date

from django.test import TestCase
from wagtail.models import Page

from apps.content.models import BlogIndexPage, BlogPage


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
