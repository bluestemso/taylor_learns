from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.bluesky.models import BlueskySourceSettings
from apps.bluesky.services.identity import resolve_handle_identity


class BlueskySourceSettingsAdminForm(forms.ModelForm):
    confirm_replace = forms.BooleanField(required=False, label="Confirm source replacement")

    class Meta:
        model = BlueskySourceSettings
        fields = ("handle", "backfill_start_date", "is_enabled", "is_active")

    def clean(self):
        cleaned_data = super().clean()
        handle = cleaned_data.get("handle")
        if not handle:
            return cleaned_data

        try:
            resolved = resolve_handle_identity(handle)
        except ValidationError as exc:
            raise forms.ValidationError(exc.messages[0]) from exc

        cleaned_data["did"] = resolved["did"]
        cleaned_data["handle"] = resolved["handle"]
        cleaned_data["profile_url"] = resolved["profile_url"]

        active_settings = BlueskySourceSettings.objects.filter(is_active=True).exclude(pk=self.instance.pk).first()
        if active_settings and resolved["did"] != active_settings.did and not cleaned_data.get("confirm_replace"):
            raise forms.ValidationError("Confirm source replacement to change the active Bluesky source.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.handle = self.cleaned_data["handle"]
        instance.did = self.cleaned_data["did"]
        instance.profile_url = self.cleaned_data["profile_url"]
        instance.verified_at = timezone.now()

        if commit:
            active_settings = BlueskySourceSettings.objects.filter(is_active=True).exclude(pk=instance.pk).first()
            if active_settings and self.cleaned_data.get("confirm_replace") and active_settings.did != instance.did:
                active_settings.is_active = False
                active_settings.save(update_fields=["is_active", "updated_at"])

            instance.save()
            self.save_m2m()

        return instance
