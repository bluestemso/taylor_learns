from django.contrib import admin, messages
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import path, reverse

from .models import GadgetSource
from .sync import sync_all_gadgets, sync_gadget_source


@admin.register(GadgetSource)
class GadgetSourceAdmin(admin.ModelAdmin):
    change_list_template = "admin/gadgets/gadgetsource/change_list.html"

    list_display = (
        "slug",
        "repo_full_name",
        "published",
        "is_hidden",
        "is_blocked",
        "is_featured",
        "display_order",
        "last_sync_status",
        "last_synced_at",
    )
    list_filter = ("published", "is_hidden", "is_blocked", "is_featured", "last_sync_status")
    ordering = ("display_order", "slug")
    search_fields = ("slug", "repo_full_name", "title", "description")
    readonly_fields = (
        "created_at",
        "updated_at",
        "last_synced_sha",
        "last_synced_at",
        "last_sync_status",
        "last_sync_error",
        "commit_url",
    )

    actions = (
        "sync_selected",
        "block_selected",
        "unblock_selected",
        "hide_selected",
        "unhide_selected",
        "feature_selected",
        "unfeature_selected",
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "sync-now/",
                self.admin_site.admin_view(self.sync_now_view),
                name="gadgets_gadgetsource_sync_now",
            )
        ]
        return custom_urls + urls

    def sync_now_view(self, request: HttpRequest):
        result = sync_all_gadgets()
        level = messages.SUCCESS if result["failed"] == 0 else messages.WARNING
        self.message_user(
            request,
            f"Sync complete. Synced: {result['synced']}, skipped: {result['skipped']}, failed: {result['failed']}.",
            level=level,
        )
        return HttpResponseRedirect(reverse("admin:gadgets_gadgetsource_changelist"))

    @admin.action(description="Sync selected gadgets now")
    def sync_selected(self, request: HttpRequest, queryset):
        synced = 0
        skipped = 0
        failed = 0
        for source in queryset:
            result = sync_gadget_source(source=source)
            status = result.get("status")
            if status == "success":
                synced += 1
            elif status == "skipped":
                skipped += 1
            else:
                failed += 1

        level = messages.SUCCESS if failed == 0 else messages.WARNING
        self.message_user(
            request,
            f"Selected gadget sync complete. Synced: {synced}, skipped: {skipped}, failed: {failed}.",
            level=level,
        )

    @admin.action(description="Block selected gadgets")
    def block_selected(self, request: HttpRequest, queryset):
        updated = queryset.update(is_blocked=True)
        self.message_user(request, f"Blocked {updated} gadget(s).", level=messages.SUCCESS)

    @admin.action(description="Unblock selected gadgets")
    def unblock_selected(self, request: HttpRequest, queryset):
        updated = queryset.update(is_blocked=False)
        self.message_user(request, f"Unblocked {updated} gadget(s).", level=messages.SUCCESS)

    @admin.action(description="Hide selected gadgets")
    def hide_selected(self, request: HttpRequest, queryset):
        updated = queryset.update(is_hidden=True)
        self.message_user(request, f"Hidden {updated} gadget(s).", level=messages.SUCCESS)

    @admin.action(description="Unhide selected gadgets")
    def unhide_selected(self, request: HttpRequest, queryset):
        updated = queryset.update(is_hidden=False)
        self.message_user(request, f"Unhid {updated} gadget(s).", level=messages.SUCCESS)

    @admin.action(description="Feature selected gadgets")
    def feature_selected(self, request: HttpRequest, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"Featured {updated} gadget(s).", level=messages.SUCCESS)

    @admin.action(description="Unfeature selected gadgets")
    def unfeature_selected(self, request: HttpRequest, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f"Unfeatured {updated} gadget(s).", level=messages.SUCCESS)
