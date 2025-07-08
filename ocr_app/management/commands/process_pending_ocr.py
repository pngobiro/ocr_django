# ocr_app/management/commands/process_pending_ocr.py
import os
import sys
from django.core.management.base import BaseCommand
from django.conf import settings
from ocr_app.models import OCRJob
from ocr_app.services import process_ocr_job

class Command(BaseCommand):
    help = 'Process pending OCR jobs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--job-id',
            type=int,
            help='Process specific job ID',
        )
        parser.add_argument(
            '--max-jobs',
            type=int,
            default=10,
            help='Maximum number of jobs to process',
        )
    
    def handle(self, *args, **options):
        if not settings.NVIDIA_API_KEY:
            self.stdout.write(
                self.style.ERROR('NVIDIA API key not configured. Please set NGC_PERSONAL_API_KEY environment variable.')
            )
            return
        
        if options['job_id']:
            # Process specific job
            try:
                job = OCRJob.objects.get(id=options['job_id'])
                self.stdout.write(f'Processing job {job.id}...')
                process_ocr_job(job.id)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully processed job {job.id}')
                )
            except OCRJob.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Job {options["job_id"]} not found')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing job {options["job_id"]}: {str(e)}')
                )
        else:
            # Process pending jobs
            pending_jobs = OCRJob.objects.filter(status='pending')[:options['max_jobs']]
            
            if not pending_jobs:
                self.stdout.write('No pending jobs to process.')
                return
            
            self.stdout.write(f'Found {len(pending_jobs)} pending jobs to process.')
            
            for job in pending_jobs:
                try:
                    self.stdout.write(f'Processing job {job.id}...')
                    process_ocr_job(job.id)
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully processed job {job.id}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error processing job {job.id}: {str(e)}')
                    )
