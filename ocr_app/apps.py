# ocr_app/apps.py
from django.apps import AppConfig


class OcrAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ocr_app'
    verbose_name = 'OCR to Word Converter'
