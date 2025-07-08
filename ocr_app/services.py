# ocr_app/services.py
import os
import requests
import io
import json
import tempfile
import base64
from datetime import datetime
from PIL import Image
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from django.utils import timezone
from django.conf import settings
from .models import OCRJob, OCRResult

def process_ocr_job(job_id):
    """
    Process an OCR job.
    
    Args:
        job_id (int): The ID of the OCRJob to process.
    """
    try:
        # Get the job
        job = OCRJob.objects.get(id=job_id)
        
        # Update status to processing
        job.status = OCRJob.Status.PROCESSING
        job.save()
        
        # Get the image file
        image_path = job.image.path
        
        # Perform OCR using NVIDIA API
        ocr_results = perform_nvidia_ocr(image_path)
        
        # Create OCRResult objects
        create_ocr_results(job, ocr_results)
        
        # Generate Word document
        word_document_path = generate_word_document(job)
        
        # Update job status to completed
        job.status = OCRJob.Status.COMPLETED
        job.completed_at = timezone.now()
        job.word_document.name = word_document_path
        job.save()
        
    except Exception as e:
        # Update job status to failed
        try:
            job.status = OCRJob.Status.FAILED
            job.error_message = str(e)
            job.save()
        except:
            pass
        
        # Re-raise the exception for logging
        raise

def perform_nvidia_ocr(image_path):
    """
    Perform OCR using NVIDIA's API.
    
    Args:
        image_path (str): Path to the image file.
        
    Returns:
        list: List of OCR results.
    """
    api_key = settings.NVIDIA_API_KEY
    
    if not api_key:
        raise ValueError("NVIDIA API key not configured")
    
    # Prepare the image
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    # API endpoint
    url = "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/ocr"
    
    # Headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Request payload
    payload = {
        "data": [
            {
                "image": encoded_image,
                "min_confidence": 0.3  # Minimum confidence threshold
            }
        ]
    }
    
    # Send request
    response = requests.post(url, headers=headers, json=payload)
    
    # Check for errors
    if response.status_code != 200:
        raise Exception(f"NVIDIA API returned status code {response.status_code}: {response.text}")
    
    # Parse response
    result = response.json()
    
    # Extract text boxes
    try:
        return result['results'][0]['boxes']
    except (KeyError, IndexError):
        raise Exception("Unexpected response format from NVIDIA API")

def create_ocr_results(job, ocr_results):
    """
    Create OCRResult objects from the OCR results.
    
    Args:
        job (OCRJob): The job object.
        ocr_results (list): List of OCR results from NVIDIA API.
    """
    # Delete existing results if any
    job.results.all().delete()
    
    # Create new results
    for result in ocr_results:
        try:
            OCRResult.objects.create(
                job=job,
                text=result['text'],
                confidence=result['confidence'],
                x1=result['vertices'][0]['x'],
                y1=result['vertices'][0]['y'],
                x2=result['vertices'][1]['x'],
                y2=result['vertices'][1]['y'],
                x3=result['vertices'][2]['x'],
                y3=result['vertices'][2]['y'],
                x4=result['vertices'][3]['x'],
                y4=result['vertices'][3]['y']
            )
        except (KeyError, IndexError) as e:
            # Skip invalid results
            continue

def generate_word_document(job):
    """
    Generate a Word document from the OCR results.
    
    Args:
        job (OCRJob): The job object.
        
    Returns:
        str: Path to the generated Word document.
    """
    # Create a new Document
    doc = Document()
    
    # Add document title
    doc.add_heading('OCR Results', level=1)
    
    # Add document info
    doc.add_paragraph(f'Processing Date: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
    doc.add_paragraph(f'Job ID: {job.id}')
    doc.add_paragraph(f'Image: {os.path.basename(job.image.name)}')
    doc.add_paragraph(f'Total Items: {job.results.count()}')
    
    # Add horizontal line
    doc.add_paragraph('_' * 50)
    
    # Add section for extracted text
    doc.add_heading('Extracted Text', level=2)
    
    # Get results ordered by vertical position
    results = job.results.all().order_by('y1')
    
    # Add the text content
    for result in results:
        p = doc.add_paragraph()
        run = p.add_run(result.text)
        run.bold = result.confidence > 0.9  # Bold text with high confidence
    
    # Add horizontal line
    doc.add_paragraph('_' * 50)
    
    # Add detailed results table
    doc.add_heading('Detailed Results', level=2)
    
    # Create table
    table = doc.add_table(rows=1, cols=4)
    table.style = 'Table Grid'
    
    # Add header row
    header_cells = table.rows[0].cells
    header_cells[0].text = 'Text'
    header_cells[1].text = 'Confidence'
    header_cells[2].text = 'Position (x, y)'
    header_cells[3].text = 'Size (w x h)'
    
    # Add data rows
    for result in results:
        row_cells = table.add_row().cells
        row_cells[0].text = result.text
        row_cells[1].text = f'{result.confidence:.3f}'
        row_cells[2].text = f'({result.x1}, {result.y1})'
        
        # Calculate width and height
        width = max(result.x2, result.x3) - min(result.x1, result.x4)
        height = max(result.y3, result.y4) - min(result.y1, result.y2)
        row_cells[3].text = f'{width} x {height}'
    
    # Save the document
    document_path = f'documents/ocr_document_{job.id}.docx'
    full_path = os.path.join(settings.MEDIA_ROOT, document_path)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    doc.save(full_path)
    
    return document_path
