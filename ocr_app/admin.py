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
        "retry_info",
        "created_at",
        "completed_at",
        "results_count",
    )
    list_filter = ("status", "created_at", "retry_count")
    search_fields = ("id", "error_message")
    readonly_fields = ("created_at", "completed_at", "image_preview", "retry_count", "last_retry_at")
    actions = ['retry_failed_jobs']
    
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
    
    def retry_info(self, obj):
        if obj.retry_count > 0:
            return format_html(
                '<span class="text-warning">{}💸/3</span>',
                obj.retry_count
            )
        return "-"
    retry_info.short_description = "Retries"

    def retry_failed_jobs(self, request, queryset):
        """Admin action to retry failed jobs."""
        retried_count = 0
        for job in queryset.filter(status=OCRJob.Status.FAILED):
            if job.can_retry():
                if job.retry_job():
                    from .services import process_ocr_job
                    import threading
                    thread = threading.Thread(target=process_ocr_job, args=(job.id,))
                    thread.daemon = True
                    thread.start()
                    retried_count += 1
        
        self.message_user(request, f'Successfully queued {retried_count} jobs for retry.')
    
    retry_failed_jobs.short_description = "Retry selected failed jobs"


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
