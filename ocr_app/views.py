# ocr_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.conf import settings

from .models import OCRJob, OCRResult
from .forms import OCRJobForm
from .services import process_ocr_job

import os
import threading
import mimetypes

class OCRJobCreateView(CreateView):
    """View for creating a new OCR job by uploading an image."""
    model = OCRJob
    form_class = OCRJobForm
    template_name = 'ocr_app/upload.html'
    success_url = reverse_lazy('ocr_job_list')
    
    def form_valid(self, form):
        """Handle successful form submission."""
        # Save the job instance
        self.object = form.save()
        
        # Start OCR processing in a background thread
        if settings.PROCESS_JOBS_ASYNC:
            thread = threading.Thread(target=process_ocr_job, args=(self.object.id,))
            thread.daemon = True
            thread.start()
        else:
            # For testing or when celery isn't available
            process_ocr_job(self.object.id)
        
        messages.success(self.request, 'Image uploaded successfully. Processing OCR...')
        return redirect(self.get_success_url())

class OCRJobListView(ListView):
    """View for listing all OCR jobs."""
    model = OCRJob
    template_name = 'ocr_app/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 12
    
    def get_queryset(self):
        """Return the list of jobs for the current user."""
        return OCRJob.objects.all().order_by('-created_at')

class OCRJobDetailView(DetailView):
    """View for displaying OCR job details."""
    model = OCRJob
    template_name = 'ocr_app/job_detail.html'
    context_object_name = 'job'

def download_word_document(request, pk):
    """View for downloading the generated Word document."""
    job = get_object_or_404(OCRJob, pk=pk)
    
    if not job.word_document:
        raise Http404("Word document not found.")
    
    file_path = job.word_document.path
    if not os.path.exists(file_path):
        raise Http404("Word document file not found.")
    
    with open(file_path, 'rb') as file:
        response = HttpResponse(
            file.read(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="ocr_document_{job.id}.docx"'
        return response

def check_job_status(request, pk):
    """AJAX endpoint for checking job status."""
    try:
        job = OCRJob.objects.get(pk=pk)
        return JsonResponse({
            'status': job.status,
            'completed': job.status not in ['pending', 'processing']
        })
    except OCRJob.DoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404)

def retry_job(request, pk):
    """View for retrying a failed OCR job."""
    job = get_object_or_404(OCRJob, pk=pk)
    
    if request.method == 'POST':
        if job.can_retry():
            if job.retry_job():
                # Start OCR processing in a background thread
                if settings.PROCESS_JOBS_ASYNC:
                    thread = threading.Thread(target=process_ocr_job, args=(job.id,))
                    thread.daemon = True
                    thread.start()
                else:
                    process_ocr_job(job.id)
                
                messages.success(request, f'Job #{job.id} has been queued for retry. Processing...')
            else:
                messages.error(request, f'Unable to retry job #{job.id}.')
        else:
            if job.status != OCRJob.Status.FAILED:
                messages.error(request, f'Job #{job.id} is not in a failed state.')
            else:
                messages.error(request, f'Job #{job.id} has exceeded the maximum retry limit (3).')
    
    return redirect('ocr_job_detail', pk=pk)
