from django.db import models
from modelcluster.fields import ParentalKey
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Orderable, Page
from wagtail.search import index

from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

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


class BlogIndexPage(BaseContentPage):
    """
    Index page for a blog
    """

    intro = RichTextField(blank=True)
    content_panels = Page.content_panels + [FieldPanel("intro", classname="full")]

    def get_ordered_blog_posts(self):
        return (
            Page.objects.live()
            .descendant_of(self)
            .specific()
            .order_by("-first_published_at")
        )


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


class PortfolioIndexPage(BaseContentPage):
    """
    Index page for the portfolio
    """

    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro", classname="full")]

    def get_projects(self):
        return self.get_children().live().order_by("-first_published_at")


class ProjectPage(BaseContentPage):
    """
    A portfolio project
    """

    date = models.DateField("Project date")
    description = RichTextField()
    project_url = models.URLField(blank=True)
    repo_url = models.URLField(blank=True)
    
    # We can use a StreamField for mixed media (images/videos) or separate InlinePanels.
    # The user mentioned "images, gifs, videos".
    # Let's use a StreamField for flexibility in the main content area, 
    # or specific fields if they want a structured gallery.
    # Given "images, gifs, videos", a StreamField is often best for mixing them.
    # But let's stick to the plan: "gallery_images (InlinePanel) ... videos (InlinePanel or StreamField)"
    # I'll add a gallery and a video block to the body or separate fields.
    # Let's add a `gallery` StreamField block or just use the existing `body` concept but tailored.
    # Actually, the plan said: "gallery_images (InlinePanel) for images/gifs. videos (InlinePanel or StreamField) for videos."
    
    body = StreamField([
        ("paragraph", blocks.RichTextBlock()),
        ("image", ImageChooserBlock()),
        ("video", blocks.URLBlock(help_text="URL to a video (e.g. YouTube, Vimeo)")),
        ("html", blocks.RawHTMLBlock()),
    ])

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
