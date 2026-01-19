from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from .models import Video

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        if not obj.video_file:
            raise ValidationError(
                {"video_file": "Video file is required."}
            )
        super().save_model(request, obj, form, change)