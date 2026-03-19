from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html

from apps.bluesky.forms import BlueskySourceSettingsAdminForm
from apps.bluesky.models import BlueskySourceSettings


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

        effective_backfill = obj.effective_backfill_start_at()
        backfill_display = f"{effective_backfill.strftime('%Y-%m-%d %H:%M:%S')} {settings.TIME_ZONE}"
        return format_html(
            "Handle: {}<br>DID: {}<br>Profile: {}<br>Backfill from: {}<br>Enabled: {}",
            obj.handle,
            obj.did,
            obj.profile_url,
            backfill_display,
            obj.is_enabled,
        )

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False
