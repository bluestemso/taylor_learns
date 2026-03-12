import json
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder
from wagtail.actions.copy_for_translation import CopyPageForTranslationAction
from wagtail.models import Locale, Page, Site

from apps.content.models import BlogIndexPage, BlogPage, ContentPage


class Command(BaseCommand):
    help = "Bootstraps your initial Wagtail / blog set up"

    def handle(self, **options):
        bootstrap_initial_content()


def bootstrap_initial_content():
    root_page = Page.objects.get(slug="root").specific
    try:
        landing_page = ContentPage.objects.get(slug="content")
        print("Using existing content homepage...")
    except ContentPage.DoesNotExist:
        print("Creating your content homepage...")
        landing_page = ContentPage(
            slug="content",
            title="Welcome to your content area!",
            body=_text_to_stream_value(
                "This is where your blog lives. You can also create other pages here. "
                'Everything here can be edited in <a href="/cms">the content admin</a>.'
            ),
        )
        root_page.add_child(instance=landing_page)
        landing_page.save()

    site = Site.objects.get()
    site.root_page = landing_page
    site.save()

    if BlogIndexPage.objects.filter(slug="blog").exists():
        blog_index = BlogIndexPage.objects.filter(slug="blog")[0]
        print("Using existing blog index page...")
    else:
        print("Creating your blog index page...")
        blog_index = BlogIndexPage(
            slug="blog",
            title="Blog",
            intro="Welcome to our blog!",
        )
        landing_page.add_child(instance=blog_index)
        blog_index.save()

    try:
        print("Creating some blog posts...")
        blog_post = BlogPage(
            slug="wagtail-content-workflow",
            title="Wagtail Content Workflow",
            date=datetime.today(),
            intro="An introduction to managing content with Wagtail",
            body=_text_to_stream_value(BLOG_POST_HTML),
        )
        save_post(blog_index, blog_post)
        blog_post_2 = BlogPage(
            slug="another-post",
            title="Another Blog Post",
            date=datetime.today() - timedelta(days=1),
            intro="A second post, with other interesting information.",
            body=_text_to_stream_value(
                'This is the body of the post. You can edit these in <a href="/cms">the content admin</a>.'
            ),
        )
        save_post(blog_index, blog_post_2)
        print("Created some blog posts...")
    except ValidationError:
        # probably already ran bootstrap
        print("Blog posts already found... leaving things alone")

    create_pages_for_translation(landing_page)


def _text_to_stream_value(text):
    return json.dumps([{"type": "paragraph", "value": text}], cls=DjangoJSONEncoder)


def save_post(blog_index, post):
    blog_index.add_child(instance=post)
    post.save()
    revision = post.save_revision()
    revision.publish()


def create_pages_for_translation(landing_page):
    locale, _ = Locale.objects.get_or_create(language_code="fr")
    try:
        landing_page_fr = CopyPageForTranslationAction(landing_page, locale, include_subtree=True).execute(
            skip_permission_checks=True
        )
        append_locale_key_to_titles(landing_page_fr.id)
    except ValidationError as e:
        print(f"Problem creating wagtail translations. Details {e}")


def append_locale_key_to_titles(page_id):
    page = Page.objects.get(id=page_id)
    print("Updating page: ", page.title)
    page.title += " (fr)"
    page.draft_title = page.title
    page.live = True
    page.has_unpublished_changes = False
    page.save()
    for child in page.get_children():
        append_locale_key_to_titles(child.id)


BLOG_POST_HTML = (
    "<h2>What is Wagtail?</h2>"
    '<p><a href="https://wagtail.org/">Wagtail</a> is a powerful CMS (Content Management System) built on top '
    "of Django. You can use it to create rich websites that can be edited through a friendly admin interface. "
    "It is great for creating marketing sites, blogs, and other mostly static content.</p>"
    "<h2>How do I use it?</h2>"
    "<p>If you're reading this page, <b>you already are</b>. This page is powered by Wagtail content blocks.</p>"
    '<p>To see it in action, head over to <a href="/cms">the content admin</a> section of your app '
    '(you will need a superuser account). Find the page titled "Wagtail Content Workflow" and try modifying '
    "it with the edit button. You can add sections, images, and more.</p>"
    "<h2>Next steps</h2>"
    "<p>Now that you've seen how easy it is to add content to your site, try creating a few more blog posts. "
    "Experiment with images, different styles of text, and embedded media.</p>"
    '<hr/><p><i>For more information, check out the </i><a href="https://docs.wagtail.org/"><i>Wagtail '
    "documentation</i></a><i>.</i></p>"
)
