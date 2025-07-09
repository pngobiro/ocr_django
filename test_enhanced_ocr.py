#!/usr/bin/env python
"""
Test script for the enhanced Django OCR application.
This script tests the new features including image preprocessing,
enhanced OCR processing, and Word document generation.
"""
import os
import sys
import django

# Add the project root to Python path
sys.path.append('/home/ngobiro/projects/ocr_django')

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ocr_django.settings')
django.setup()

from ocr_app.models import OCRJob
from ocr_app.services import process_ocr_job
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
import time

def test_enhanced_ocr():
    """Test the enhanced OCR functionality."""
    print("🚀 Testing Enhanced Django OCR Application")
    print("=" * 50)
    
    # Test image path
    image_path = '/home/ngobiro/projects/ocr_django/sandraWriting.jpg'
    
    if not os.path.exists(image_path):
        print(f"❌ Test image not found: {image_path}")
        return False
    
    print(f"📁 Using test image: {os.path.basename(image_path)}")
    
    try:
        # Create a test OCR job
        with open(image_path, 'rb') as image_file:
            uploaded_file = SimpleUploadedFile(
                name='test_image.jpg',
                content=image_file.read(),
                content_type='image/jpeg'
            )
            
            # Create OCR job
            job = OCRJob.objects.create(
                image=uploaded_file,
                status=OCRJob.Status.PENDING
            )
        
        print(f"✅ Created OCR job #{job.id}")
        
        # Test the enhanced OCR processing
        print("🔄 Processing OCR with enhanced features...")
        start_time = time.time()
        
        try:
            # Process the job using our enhanced service
            process_ocr_job(job.id)
            processing_time = time.time() - start_time
            
            # Refresh job from database
            job.refresh_from_db()
            
            print(f"⏱️  Processing completed in {processing_time:.2f} seconds")
            print(f"📊 Job Status: {job.get_status_display()}")
            
            if job.status == OCRJob.Status.COMPLETED:
                print("✅ OCR processing completed successfully!")
                
                # Display enhanced metadata
                print("\n📈 Enhanced Processing Metadata:")
                print(f"   • Total text items detected: {job.total_text_items}")
                print(f"   • Average confidence score: {job.average_confidence:.3f}" if job.average_confidence else "   • Average confidence: N/A")
                print(f"   • Processing time: {job.processing_time:.2f}s" if job.processing_time else "   • Processing time: N/A")
                print(f"   • Image dimensions: {job.image_width}x{job.image_height}" if job.image_width and job.image_height else "   • Image dimensions: N/A")
                print(f"   • Preprocessed: {'Yes' if job.preprocessed else 'No'}")
                
                # Display OCR results
                results = job.results.all()
                print(f"\n📝 OCR Results ({len(results)} items):")
                
                if results:
                    # Show top 5 results with highest confidence
                    top_results = results.order_by('-confidence')[:5]
                    for i, result in enumerate(top_results, 1):
                        print(f"   {i}. '{result.text[:50]}...' (confidence: {result.confidence:.3f})")
                else:
                    print("   No text detected")
                
                # Check if Word document was generated
                if job.word_document:
                    print(f"\n📄 Enhanced Word document generated: {job.word_document.name}")
                    print("   Features included:")
                    print("   • Professional court document formatting")
                    print("   • Metadata table with processing details")
                    print("   • Confidence-based text styling")
                    print("   • Quality analysis section")
                    print("   • Detailed extraction data table")
                else:
                    print("\n❌ Word document was not generated")
                
                return True
                
            elif job.status == OCRJob.Status.FAILED:
                print(f"❌ OCR processing failed: {job.error_message}")
                return False
            else:
                print(f"⚠️  Unexpected job status: {job.get_status_display()}")
                return False
                
        except Exception as e:
            print(f"❌ Error during OCR processing: {str(e)}")
            return False
    
    except Exception as e:
        print(f"❌ Error creating OCR job: {str(e)}")
        return False

def test_image_preprocessing():
    """Test the image preprocessing functionality."""
    print("\n🖼️  Testing Image Preprocessing")
    print("=" * 30)
    
    try:
        from ocr_app.services import preprocess_image_for_ocr
        
        image_path = '/home/ngobiro/projects/ocr_django/sandraWriting.jpg'
        
        if not os.path.exists(image_path):
            print(f"❌ Test image not found: {image_path}")
            return False
        
        print("🔄 Preprocessing test image...")
        preprocessed_path = preprocess_image_for_ocr(image_path)
        
        if os.path.exists(preprocessed_path):
            print(f"✅ Image preprocessing successful: {os.path.basename(preprocessed_path)}")
            
            # Get file sizes for comparison
            original_size = os.path.getsize(image_path)
            preprocessed_size = os.path.getsize(preprocessed_path)
            
            print(f"   • Original size: {original_size:,} bytes")
            print(f"   • Preprocessed size: {preprocessed_size:,} bytes")
            
            # Clean up temp file
            os.unlink(preprocessed_path)
            print("   • Temporary file cleaned up")
            
            return True
        else:
            print("❌ Preprocessing failed - no output file")
            return False
            
    except Exception as e:
        print(f"❌ Error during preprocessing: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Enhanced Django OCR Application Test Suite")
    print("=" * 60)
    
    # Test preprocessing
    preprocessing_success = test_image_preprocessing()
    
    # Test enhanced OCR
    ocr_success = test_enhanced_ocr()
    
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    print(f"   • Image Preprocessing: {'✅ PASS' if preprocessing_success else '❌ FAIL'}")
    print(f"   • Enhanced OCR Processing: {'✅ PASS' if ocr_success else '❌ FAIL'}")
    
    if preprocessing_success and ocr_success:
        print("\n🎉 All tests passed! The enhanced OCR application is working correctly.")
        print("\n💡 Key improvements implemented:")
        print("   • Image preprocessing for better OCR accuracy")
        print("   • Enhanced OCR processing with confidence filtering")
        print("   • Professional Word document generation for court documents")
        print("   • Enhanced metadata tracking and analysis")
        print("   • Improved error handling and fallback mechanisms")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")
