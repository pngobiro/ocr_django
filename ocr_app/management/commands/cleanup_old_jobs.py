# ocr_app/management/commands/cleanup_old_jobs.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from ocr_app.models import OCRJob


class Command(BaseCommand):
    help = "Clean up old OCR jobs and their files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Delete jobs older than this many days",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        cutoff_date = timezone.now() - timedelta(days=options["days"])
        old_jobs = OCRJob.objects.filter(created_at__lt=cutoff_date)

        if not old_jobs.exists():
            self.stdout.write("No old jobs to clean up.")
            return

        self.stdout.write(
            f'Found {old_jobs.count()} jobs older than {options["days"]} days.'
        )

        if options["dry_run"]:
            self.stdout.write("DRY RUN - Would delete:")
            for job in old_jobs:
                self.stdout.write(f"  - Job {job.id} (created: {job.created_at})")
        else:
            deleted_count = 0
            for job in old_jobs:
                try:
                    # Delete associated files
                    if job.image:
                        job.image.delete()
                    if job.word_document:
                        job.word_document.delete()

                    job.delete()
                    deleted_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error deleting job {job.id}: {str(e)}")
                    )

            self.stdout.write(
                self.style.SUCCESS(f"Successfully deleted {deleted_count} old jobs.")
            )
