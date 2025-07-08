# ocr_app/management/commands/test_nvidia_api.py
import os
import requests
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Test NVIDIA API connection'
    
    def handle(self, *args, **options):
        api_key = settings.NVIDIA_API_KEY
        
        if not api_key:
            self.stdout.write(
                self.style.ERROR('NVIDIA API key not configured. Please set NGC_PERSONAL_API_KEY environment variable.')
            )
            return
        
        # Test assets endpoint
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "accept": "application/json",
            }
            
            self.stdout.write('Testing NVIDIA API connection...')
            
            # Test with a simple request to the assets endpoint
            response = requests.get(
                "https://api.nvcf.nvidia.com/v2/nvcf/assets",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.stdout.write(
                    self.style.SUCCESS('✓ NVIDIA API connection successful!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ API returned status code: {response.status_code}')
                )
                self.stdout.write(f'Response: {response.text}')
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Connection error: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Unexpected error: {str(e)}')
            )
