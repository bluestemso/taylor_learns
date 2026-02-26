import os
import sys

import django
from django.utils import timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taylor_learns.settings")
django.setup()

from wagtail.models import Page  # noqa: E402

from apps.content.models import (  # noqa: E402
    BlogIndexPage,
    ExternalLinkPage,
    MicroPostPage,
    PortfolioIndexPage,
    ProjectPage,
)


def run():
    # Ensure root page exists
    root = Page.get_first_root_node()

    # Create BlogIndexPage if not exists
    if not BlogIndexPage.objects.exists():
        blog_index = BlogIndexPage(title="Blog", slug="blog", intro="Welcome to my blog")
        root.add_child(instance=blog_index)
        blog_index.save_revision().publish()
        print("Created BlogIndexPage")
    else:
        blog_index = BlogIndexPage.objects.first()
        print("Found BlogIndexPage")

    # Create MicroPostPage
    if not MicroPostPage.objects.filter(title="Micro Post Test").exists():
        micro_post = MicroPostPage(
            title="Micro Post Test",
            slug="micro-post-test",
            date=timezone.now().date(),
            body=[("paragraph", "This is a micro post.")],
        )
        blog_index.add_child(instance=micro_post)
        micro_post.save_revision().publish()
        print("Created MicroPostPage")

    # Create ExternalLinkPage
    if not ExternalLinkPage.objects.filter(title="External Link Test").exists():
        link_page = ExternalLinkPage(
            title="External Link Test",
            slug="external-link-test",
            date=timezone.now().date(),
            link_url="https://example.com",
            commentary="This is a cool link.",
            quote="Best link ever.",
        )
        blog_index.add_child(instance=link_page)
        link_page.save_revision().publish()
        print("Created ExternalLinkPage")

    # Create PortfolioIndexPage
    if not PortfolioIndexPage.objects.exists():
        portfolio_index = PortfolioIndexPage(title="Portfolio", slug="portfolio", intro="My projects")
        root.add_child(instance=portfolio_index)
        portfolio_index.save_revision().publish()
        print("Created PortfolioIndexPage")
    else:
        portfolio_index = PortfolioIndexPage.objects.first()
        print("Found PortfolioIndexPage")

    # Create ProjectPage
    if not ProjectPage.objects.filter(title="Project Test").exists():
        project_page = ProjectPage(
            title="Project Test",
            slug="project-test",
            date=timezone.now().date(),
            description="A test project",
            project_url="https://project.com",
            repo_url="https://github.com/project",
            body=[("paragraph", "Project details.")],
        )
        portfolio_index.add_child(instance=project_page)
        project_page.save_revision().publish()
        print("Created ProjectPage")


if __name__ == "__main__":
    try:
        run()
        print("Verification successful!")
    except Exception as e:
        print(f"Verification failed: {e}")
        exit(1)
