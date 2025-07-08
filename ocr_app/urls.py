# ocr_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.OCRJobListView.as_view(), name='ocr_job_list'),
    path('upload/', views.OCRJobCreateView.as_view(), name='ocr_job_create'),
    path('job/<int:pk>/', views.OCRJobDetailView.as_view(), name='ocr_job_detail'),
    path('download/<int:pk>/', views.download_word_document, name='download_word_document'),
    path('status/<int:pk>/', views.check_job_status, name='check_job_status'),
]
