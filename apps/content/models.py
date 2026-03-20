from datetime import UTC, datetime
from datetime import date as date_value

from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Orderable, Page
from wagtail.search import index

from apps.content.blocks import CaptionBlock


def _get_default_block_types():
    return [
        ("paragraph", blocks.RichTextBlock()),
        ("image", ImageChooserBlock()),
        ("caption", CaptionBlock()),
        ("html", blocks.RawHTMLBlock()),
    ]


class BaseContentPage(Page):
    social_image = models.ImageField(null=True, blank=True, help_text="The image to use in social sharing metadata.")
    tags = ClusterTaggableManager(through="content.ContentPageTag", blank=True)

    promote_panels = Page.promote_panels + [
        FieldPanel("social_image"),
        FieldPanel("tags"),
    ]

    def get_social_image_url(self):
        if self.social_image:
            return self.social_image.url
        return ""

    class Meta:
        abstract = True


class ContentPageTag(TaggedItemBase):
    content_object = ParentalKey("wagtailcore.Page", on_delete=models.CASCADE, related_name="content_tagged_items")


class ContentPage(BaseContentPage):
    """
    A page of generic content, for example an 'About' or 'Contact' page.
    """

    body = StreamField(_get_default_block_types())
    content_panels = Page.content_panels + [
        FieldPanel("body", classname="full"),
    ]


class ProfilePage(BaseContentPage):
    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    intro = models.TextField(default="I'm Taylor Schaack - an operator turned software builder.")
    background = models.TextField(
        default=(
            "My background is unusual by design: I've led operations, sales, and large cross-functional "
            "initiatives, and now I apply that same ownership to software delivery. I'm strongest at turning "
            "messy, real-world requirements into clear technical workflows that people actually use."
        )
    )
    focus = models.TextField(
        default=(
            "I'm currently focused on full-stack agentic engineering and solutions/implementation roles where I "
            "can keep shipping, keep learning, and contribute to products with real customer impact."
        )
    )
    connect = models.TextField(
        default=(
            "If you're building something meaningful and need someone who can connect product, business, and "
            "engineering execution, I'd love to connect."
        )
    )

    content_panels = Page.content_panels + [
        FieldPanel("hero_image"),
        FieldPanel("intro"),
        FieldPanel("background"),
        FieldPanel("focus"),
        FieldPanel("connect"),
    ]


class BlogIndexPage(BaseContentPage):
    """
    Index page for a blog
    """

    intro = RichTextField(blank=True)
    content_panels = Page.content_panels + [FieldPanel("intro", classname="full")]

    def get_ordered_blog_posts(self):
        posts = list(Page.objects.live().descendant_of(self).specific())

        def sort_key(post):
            published_at = post.first_published_at or datetime.min.replace(tzinfo=UTC)
            content_date = getattr(post, "date", None) or published_at.date() or date_value.min
            return (content_date, published_at, post.id or 0)

        return sorted(posts, key=sort_key, reverse=True)


class BlogPage(BaseContentPage):
    """
    A single blog post
    """

    date = models.DateField("Post date")
    intro = models.CharField(max_length=250, blank=True, null=True)
    body = StreamField(_get_default_block_types())

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
        InlinePanel("gallery_images", label="Gallery images"),
    ]

    @property
    def main_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.image
        else:
            return None

    def get_template_type(self):
        return "blog"


class BlogPageGalleryImage(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name="gallery_images")
    image = models.ForeignKey("wagtailimages.Image", on_delete=models.CASCADE, related_name="+")
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        FieldPanel("image"),
        FieldPanel("caption"),
    ]


class MicroPostPage(BaseContentPage):
    """
    A microblog post, similar to a tweet
    """

    date = models.DateField("Post date")
    body = StreamField(
        [
            ("paragraph", blocks.RichTextBlock()),
            ("image", ImageChooserBlock()),
        ]
    )

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("body", classname="full"),
    ]

    parent_page_types = ["content.BlogIndexPage"]

    def get_template_type(self):
        return "micropost"


class ExternalLinkPage(BaseContentPage):
    """
    A link to an external resource with commentary
    """

    date = models.DateField("Post date")
    link_url = models.URLField()
    commentary = RichTextField()
    quote = RichTextField(blank=True, help_text="A quote from the linked resource")

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("link_url"),
        FieldPanel("commentary"),
        FieldPanel("quote"),
    ]

    parent_page_types = ["content.BlogIndexPage"]

    def get_template_type(self):
        return "external_link"


class PortfolioIndexPage(BaseContentPage):
    """
    Index page for the portfolio
    """

    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro", classname="full")]

    def get_projects(self):
        return self.get_children().live().specific().select_related("content_type").order_by("-first_published_at")


class ProjectPage(BaseContentPage):
    """
    A portfolio project
    """

    date = models.DateField("Project date")
    description = RichTextField()
    project_url = models.URLField(blank=True)
    repo_url = models.URLField(blank=True)

    body = StreamField(
        [
            ("paragraph", blocks.RichTextBlock()),
            ("image", ImageChooserBlock()),
            ("video", blocks.URLBlock(help_text="URL to a video (e.g. YouTube, Vimeo)")),
            ("html", blocks.RawHTMLBlock()),
        ]
    )

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("description"),
        FieldPanel("project_url"),
        FieldPanel("repo_url"),
        FieldPanel("body"),
        InlinePanel("project_images", label="Project images"),
    ]

    parent_page_types = ["content.PortfolioIndexPage"]


class ProjectPageImage(Orderable):
    page = ParentalKey(ProjectPage, on_delete=models.CASCADE, related_name="project_images")
    image = models.ForeignKey("wagtailimages.Image", on_delete=models.CASCADE, related_name="+")
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        FieldPanel("image"),
        FieldPanel("caption"),
    ]
