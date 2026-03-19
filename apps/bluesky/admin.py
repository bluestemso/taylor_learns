from django.contrib import admin

from apps.bluesky.forms import BlueskySourceSettingsAdminForm
from apps.bluesky.models import BlueskySourceSettings


@admin.register(BlueskySourceSettings)
class BlueskySourceSettingsAdmin(admin.ModelAdmin):
    form = BlueskySourceSettingsAdminForm

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False
