# ocr_app/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
import os
import uuid

def image_upload_path(instance, filename):
    """Generate a unique path for uploaded images."""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads', filename)

def document_upload_path(instance, filename):
    """Generate a unique path for generated Word documents."""
    return os.path.join('documents', f"ocr_document_{instance.id}.docx")

class OCRJob(models.Model):
    """Model representing an OCR processing job."""
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PROCESSING = 'processing', _('Processing')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
    
    image = models.ImageField(upload_to=image_upload_path, 
                             verbose_name=_("Image"),
                             help_text=_("Upload an image containing text"))
    
    status = models.CharField(max_length=20, 
                              choices=Status.choices,
                              default=Status.PENDING,
                              verbose_name=_("Status"))
    
    created_at = models.DateTimeField(auto_now_add=True, 
                                     verbose_name=_("Created at"))
    
    completed_at = models.DateTimeField(null=True, 
                                       blank=True,
                                       verbose_name=_("Completed at"))
    
    error_message = models.TextField(null=True, 
                                    blank=True,
                                    verbose_name=_("Error message"))
    
    word_document = models.FileField(upload_to=document_upload_path,
                                    null=True,
                                    blank=True,
                                    verbose_name=_("Word document"))
    
    retry_count = models.IntegerField(default=0,
                                     verbose_name=_("Retry count"),
                                     help_text=_("Number of times this job has been retried"))
    
    last_retry_at = models.DateTimeField(null=True,
                                        blank=True,
                                        verbose_name=_("Last retry at"))
    
    # OCR processing metadata
    processing_time = models.FloatField(null=True, 
                                      blank=True,
                                      verbose_name=_("Processing time (seconds)"))
    
    total_text_items = models.IntegerField(default=0,
                                         verbose_name=_("Total text items found"))
    
    average_confidence = models.FloatField(null=True,
                                         blank=True,
                                         verbose_name=_("Average confidence score"))
    
    # Image metadata
    image_width = models.IntegerField(null=True, blank=True)
    image_height = models.IntegerField(null=True, blank=True)
    
    # Processing optimization flags
    preprocessed = models.BooleanField(default=False,
                                     verbose_name=_("Image was preprocessed"))
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("OCR Job")
        verbose_name_plural = _("OCR Jobs")
    
    def __str__(self):
        return f"OCR Job #{self.id} ({self.get_status_display()})"
    
    def delete(self, *args, **kwargs):
        """Delete associated files when deleting the job."""
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        
        if self.word_document:
            if os.path.isfile(self.word_document.path):
                os.remove(self.word_document.path)
        
        super().delete(*args, **kwargs)
    
    def can_retry(self):
        """Check if the job can be retried."""
        return self.status == self.Status.FAILED and self.retry_count < 3
    
    def retry_job(self):
        """Reset the job for retry."""
        if self.can_retry():
            from django.utils import timezone
            self.status = self.Status.PENDING
            self.error_message = None
            self.retry_count += 1
            self.last_retry_at = timezone.now()
            self.save()
            return True
        return False

class OCRResult(models.Model):
    """Model representing a single text item detected by OCR."""
    
    job = models.ForeignKey(OCRJob, 
                           on_delete=models.CASCADE,
                           related_name='results',
                           verbose_name=_("OCR Job"))
    
    text = models.TextField(verbose_name=_("Text content"))
    
    confidence = models.FloatField(verbose_name=_("Confidence score"),
                                  help_text=_("OCR confidence score (0-1)"))
    
    # Bounding box coordinates (top-left, top-right, bottom-right, bottom-left)
    x1 = models.IntegerField(verbose_name=_("X1"))
    y1 = models.IntegerField(verbose_name=_("Y1"))
    x2 = models.IntegerField(verbose_name=_("X2"))
    y2 = models.IntegerField(verbose_name=_("Y2"))
    x3 = models.IntegerField(verbose_name=_("X3"))
    y3 = models.IntegerField(verbose_name=_("Y3"))
    x4 = models.IntegerField(verbose_name=_("X4"))
    y4 = models.IntegerField(verbose_name=_("Y4"))
    
    class Meta:
        ordering = ['y1']  # Order by vertical position (top to bottom)
        verbose_name = _("OCR Result")
        verbose_name_plural = _("OCR Results")
    
    def __str__(self):
        return f"Text: {self.text[:30]}..." if len(self.text) > 30 else f"Text: {self.text}"
