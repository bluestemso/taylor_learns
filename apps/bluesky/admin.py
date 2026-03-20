from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html

from apps.bluesky.forms import BlueskySourceSettingsAdminForm
from apps.bluesky.models import BlueskySourceSettings, BlueskySyncRun


@admin.register(BlueskySourceSettings)
class BlueskySourceSettingsAdmin(admin.ModelAdmin):
    form = BlueskySourceSettingsAdminForm
    list_display = ("handle", "backfill_start_date", "is_enabled", "did", "verified_at", "updated_at")
    readonly_fields = ("did", "profile_url", "verified_at", "effective_settings")
    fieldsets = (
        (None, {"fields": ("handle", "backfill_start_date", "is_enabled", "confirm_replace")}),
        ("Resolved source settings", {"fields": ("did", "profile_url", "verified_at", "effective_settings")}),
    )

    @admin.display(description="Effective settings")
    def effective_settings(self, obj):
        if obj is None:
            return "-"

        backfill_display = "-"
        if obj.backfill_start_date:
            effective_backfill = obj.effective_backfill_start_at()
            backfill_display = f"{effective_backfill.strftime('%Y-%m-%d %H:%M:%S')} {settings.TIME_ZONE}"

        handle = obj.handle or "-"
        did = obj.did or "-"
        profile_url = obj.profile_url or "-"
        return format_html(
            "Handle: {}<br>DID: {}<br>Profile: {}<br>Backfill from: {}<br>Enabled: {}",
            handle,
            did,
            profile_url,
            backfill_display,
            obj.is_enabled,
        )

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BlueskySyncRun)
class BlueskySyncRunAdmin(admin.ModelAdmin):
    list_display = (
        "source_handle",
        "completed_at",
        "imported_count",
        "updated_count",
        "removed_count",
        "skipped_count",
        "failed_count",
    )
    list_select_related = ("source_settings",)
    ordering = ("-completed_at", "-created_at")

    @admin.display(description="Source")
    def source_handle(self, obj):
        return obj.source_settings.handle
