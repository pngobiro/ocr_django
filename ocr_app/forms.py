# ocr_app/forms.py
from django import forms
from .models import OCRJob

class OCRJobForm(forms.ModelForm):
    """Form for creating a new OCR job."""
    
    class Meta:
        model = OCRJob
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'image-upload',
                'style': 'display: none;'
            }),
        }
        
    def clean_image(self):
        """Validate the uploaded image."""
        image = self.cleaned_data.get('image')
        
        if image:
            # Check file size (10MB limit)
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError('The image is too large. Maximum size is 10MB.')
            
            # Check file extension
            ext = image.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                raise forms.ValidationError('Unsupported file format. Please upload JPG, PNG, GIF, or BMP images.')
        
        return image
