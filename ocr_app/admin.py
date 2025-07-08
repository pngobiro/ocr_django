# ocr_app/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import OCRJob, OCRResult


@admin.register(OCRJob)
class OCRJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "image_preview",
        "status",
        "created_at",
        "completed_at",
        "results_count",
    )
    list_filter = ("status", "created_at")
    search_fields = ("id", "error_message")
    readonly_fields = ("created_at", "completed_at", "image_preview")

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.image.url,
            )
        return "No image"

    image_preview.short_description = "Image"

    def results_count(self, obj):
        return obj.results.count()

    results_count.short_description = "Text Items"


@admin.register(OCRResult)
class OCRResultAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "text_preview", "confidence", "position")
    list_filter = ("job__status", "confidence")
    search_fields = ("text", "job__id")

    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    text_preview.short_description = "Text"

    def position(self, obj):
        return f"({obj.x1}, {obj.y1})"

    position.short_description = "Position"
