import os
import sys
import uuid
import zipfile

import requests
from django.core.management.base import BaseCommand


# NVAI endpoint for the ocdrnet NIM
nvai_url="https://ai.api.nvidia.com/v1/cv/nvidia/ocdrnet"

header_auth = f"Bearer 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"


def _upload_asset(input, description):
    """
    Uploads an asset to the NVCF API.
    :param input: The binary asset to upload
    :param description: A description of the asset

    """
    assets_url = "https://api.nvcf.nvidia.com/v2/nvcf/assets"

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
        data=input,
        headers=s3_headers,
        timeout=300,
    )

    response.raise_for_status()
    return uuid.UUID(asset_id)


class Command(BaseCommand):
    help = 'Test NVIDIA OCR API connectivity and functionality using the exact user-provided code'

    def add_arguments(self, parser):
        parser.add_argument('image_path', type=str, help='Path to the image file to process')
        parser.add_argument('output_dir', type=str, help='Output directory for results')

    def handle(self, *args, **options):
        """Uploads an image of your choosing to the NVCF API and sends a
        request to the Optical character detection and recognition model.
        The response is saved to a local directory.

        Note: You must set up an environment variable, NGC_PERSONAL_API_KEY.
        """
        
        image_path = options['image_path']
        output_dir = options['output_dir']

        self.stdout.write(f"Testing NVIDIA OCR API with image: {image_path}")
        self.stdout.write(f"Output directory: {output_dir}")

        # Check if image file exists
        if not os.path.exists(image_path):
            self.stdout.write(
                self.style.ERROR(f'Image file not found: {image_path}')
            )
            return

        try:
            asset_id = _upload_asset(open(image_path, "rb"), "Input Image")

            inputs = {"image": f"{asset_id}", "render_label": False}

            asset_list = f"{asset_id}"

            headers = {
                "Content-Type": "application/json",
                "NVCF-INPUT-ASSET-REFERENCES": asset_list,
                "NVCF-FUNCTION-ASSET-IDS": asset_list,
                "Authorization": header_auth,
            }

            response = requests.post(nvai_url, headers=headers, json=inputs)

            with open(f"{output_dir}.zip", "wb") as out:
                out.write(response.content)

            with zipfile.ZipFile(f"{output_dir}.zip", "r") as z:
                z.extractall(output_dir)

            self.stdout.write(self.style.SUCCESS(f"Output saved to {output_dir}"))
            self.stdout.write(f"Files in output directory: {os.listdir(output_dir)}")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during OCR processing: {str(e)}')
            )
