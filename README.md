# OCR to Word Converter

This is a Django-based web application that allows users to upload images, process them using NVIDIA's OCR technology, and download the extracted text as a Microsoft Word document.

## Key Features

- **Modern Web Interface:** A clean and responsive user interface built with Bootstrap 5, featuring an image upload form, job list, and detailed job views.
- **NVIDIA OCR Integration:** Securely integrates with the NVIDIA AI Platform for high-accuracy text recognition, including confidence scores and text coordinates.
- **Microsoft Word Generation:** Automatically generates professionally formatted Word documents containing the extracted text, processing metadata, and a detailed results table.
- **Background Job Processing:** Utilizes asynchronous tasks to handle OCR processing in the background, allowing users to track job statuses (pending, processing, completed, failed) in real-time.
- **Django Admin Integration:** Provides a comprehensive admin interface for managing OCR jobs, viewing results, and filtering by status.
- **Management Commands:** Includes custom Django management commands for processing pending jobs, cleaning up old files, and testing the NVIDIA API connection.

## Technology Stack

- **Backend:** Django, Python
- **Frontend:** HTML, Bootstrap, JavaScript
- **OCR Engine:** NVIDIA AI Platform
- **Database:** SQLite (default)

## Project Structure

```
ocr_django/
├── ocr_django/         # Django project directory
│   ├── settings.py
│   └── urls.py
├── ocr_app/            # Main application directory
│   ├── migrations/
│   ├── templates/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── manage.py           # Django's command-line utility
└── README.md
```

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/pngobiro/ocr_django.git
    cd ocr_django
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the project root and add the following:
    ```
    NVIDIA_API_KEY="your_nvidia_api_key"
    SECRET_KEY="your_django_secret_key"
    ```

5.  **Run database migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Create a superuser:**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Run the development server:**
    ```bash
    python manage.py runserver
    ```

## Usage

- Access the web application by navigating to `http://127.0.0.1:8000/` in your browser.
- Upload an image containing text.
- Monitor the job status on the "OCR Jobs" page.
- Once the job is complete, download the generated Word document from the job detail page.

## Management Commands

- **Process pending OCR jobs:**
  ```bash
  python manage.py process_pending_ocr
  ```
- **Clean up old jobs (e.g., older than 30 days):**
  ```bash
  python manage.py cleanup_old_jobs --days 30
  ```
- **Test the NVIDIA API connection:**
  ```bash
  python manage.py test_nvidia_api
  ```
