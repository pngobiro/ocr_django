# ocr_app/services.py
import os
import requests
import json
from datetime import datetime
from PIL import Image
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from django.utils import timezone
from django.conf import settings
from .models import OCRJob, OCRResult

def _upload_asset(input_data, description):
    """
    Uploads an asset to the NVCF API - exactly as per working example.
    :param input_data: The binary asset to upload
    :param description: A description of the asset
    """
    api_key = settings.NVIDIA_API_KEY
    if not api_key:
        raise ValueError("NVIDIA API key not configured")
        
    assets_url = "https://api.nvcf.nvidia.com/v2/nvcf/assets"
    header_auth = f"Bearer {api_key}"

    headers = {
        "Authorization": header_auth,
        "Content-Type": "application/json",
        "accept": "application/json",
    }

    s3_headers = {
        "x-amz-meta-nvcf-asset-description": description,
        "content-type": "image/jpeg",
    }

    payload = {"contentType": "image/jpeg", "description": description}

    response = requests.post(assets_url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    asset_url = response.json()["uploadUrl"]
    asset_id = response.json()["assetId"]

    response = requests.put(
        asset_url,
        data=input_data,
        headers=s3_headers,
        timeout=300,
    )
    response.raise_for_status()
    return asset_id

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
    Perform OCR using NVIDIA's OCDRNet API - exactly as per working example.
    
    Args:
        image_path (str): Path to the image file.
        
    Returns:
        list: List of OCR results.
    """
    api_key = settings.NVIDIA_API_KEY
    
    if not api_key:
        raise ValueError("NVIDIA API key not configured")
    
    # NVAI endpoint for the ocdrnet NIM - exact from working code
    nvai_url = "https://ai.api.nvidia.com/v1/cv/nvidia/ocdrnet"
    header_auth = f"Bearer {api_key}"
    
    # Upload the asset - exactly as in working code
    with open(image_path, "rb") as image_file:
        asset_id = _upload_asset(image_file.read(), "Input Image")
    
    # Prepare the request - exactly as in working code
    inputs = {"image": f"{asset_id}", "render_label": False}
    asset_list = f"{asset_id}"
    
    headers = {
        "Content-Type": "application/json",
        "NVCF-INPUT-ASSET-REFERENCES": asset_list,
        "NVCF-FUNCTION-ASSET-IDS": asset_list,
        "Authorization": header_auth,
    }
    
    # Send request to NVIDIA OCR API - exactly as in working code
    response = requests.post(nvai_url, headers=headers, json=inputs)
    
    # Check for errors
    if response.status_code != 200:
        raise Exception(f"NVIDIA API returned status code {response.status_code}: {response.text}")
    
    # Parse JSON response directly - as per your working Python code
    try:
        response_data = response.json()
        ocr_results = []
        
        # Process the response based on the actual format
        if 'data' in response_data:
            for item in response_data['data']:
                if 'object' in item and item['object'] == 'text_detection':
                    text = item.get('text', '').strip()
                    confidence = item.get('confidence', 0.0)
                    bbox = item.get('bbox', {})
                    
                    if text:  # Only add non-empty text
                        result = {
                            'text': text,
                            'confidence': float(confidence),
                            'vertices': format_bbox_to_vertices(bbox)
                        }
                        ocr_results.append(result)
        
        # Alternative format handling
        elif 'predictions' in response_data:
            for prediction in response_data['predictions']:
                text = prediction.get('text', '').strip()
                confidence = prediction.get('confidence', 0.0)
                bbox = prediction.get('bbox', prediction.get('box', {}))
                
                if text:
                    result = {
                        'text': text,
                        'confidence': float(confidence),
                        'vertices': format_bbox_to_vertices(bbox)
                    }
                    ocr_results.append(result)
        
        # If direct format
        elif isinstance(response_data, list):
            for item in response_data:
                text = item.get('text', '').strip()
                confidence = item.get('confidence', 0.0)
                bbox = item.get('bbox', item.get('box', {}))
                
                if text:
                    result = {
                        'text': text,
                        'confidence': float(confidence),
                        'vertices': format_bbox_to_vertices(bbox)
                    }
                    ocr_results.append(result)
        
        return ocr_results
        
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON response: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing OCR response: {str(e)}")

def format_bbox_to_vertices(bbox):
    """
    Convert bounding box to vertices format for OCR results.
    
    Args:
        bbox (dict): Bounding box coordinates
        
    Returns:
        list: List of vertex coordinates
    """
    if not bbox:
        # Default fallback
        return [
            {'x': 0, 'y': 0},
            {'x': 100, 'y': 0},
            {'x': 100, 'y': 20},
            {'x': 0, 'y': 20}
        ]
    
    # Handle different bbox formats
    if 'x' in bbox and 'y' in bbox and 'width' in bbox and 'height' in bbox:
        # Format: {x, y, width, height}
        x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
        return [
            {'x': int(x), 'y': int(y)},
            {'x': int(x + w), 'y': int(y)},
            {'x': int(x + w), 'y': int(y + h)},
            {'x': int(x), 'y': int(y + h)}
        ]
    elif 'x1' in bbox and 'y1' in bbox and 'x2' in bbox and 'y2' in bbox:
        # Format: {x1, y1, x2, y2}
        x1, y1, x2, y2 = bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']
        return [
            {'x': int(x1), 'y': int(y1)},
            {'x': int(x2), 'y': int(y1)},
            {'x': int(x2), 'y': int(y2)},
            {'x': int(x1), 'y': int(y2)}
        ]
    elif isinstance(bbox, list) and len(bbox) >= 4:
        # Format: [x1, y1, x2, y2]
        x1, y1, x2, y2 = bbox[:4]
        return [
            {'x': int(x1), 'y': int(y1)},
            {'x': int(x2), 'y': int(y1)},
            {'x': int(x2), 'y': int(y2)},
            {'x': int(x1), 'y': int(y2)}
        ]
    
    # Default fallback
    return [
        {'x': 0, 'y': 0},
        {'x': 100, 'y': 0},
        {'x': 100, 'y': 20},
        {'x': 0, 'y': 20}
    ]

def extract_text_from_json(data):
    """
    This function is kept for compatibility but is no longer used.
    The new implementation directly parses JSON in perform_nvidia_ocr.
    """
    return []
def format_coordinates(coords):
    """
    Format coordinates to the expected vertex format.
    This function is kept for compatibility but format_bbox_to_vertices is preferred.
    """
    return format_bbox_to_vertices(coords)

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
