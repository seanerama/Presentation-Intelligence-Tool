"""
URL Downloader Module
Downloads presentation files from URLs.
"""

import os
import requests
from typing import Dict, Optional
from urllib.parse import urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_file_from_url(url: str, output_dir: str, timeout: int = 30) -> Dict[str, any]:
    """
    Download a file from a URL.

    Args:
        url: URL to download from
        output_dir: Directory to save the downloaded file
        timeout: Request timeout in seconds

    Returns:
        {
            'success': bool,
            'file_path': str,  # Path to downloaded file
            'filename': str,  # Original filename
            'error': str  # Error message if failed
        }
    """
    try:
        logger.info(f"Downloading file from URL: {url}")

        # Parse URL to extract filename
        parsed_url = urlparse(url)
        url_path = parsed_url.path

        # Get filename from URL
        filename = os.path.basename(url_path)

        # Validate file extension
        if not filename or not any(filename.lower().endswith(ext) for ext in ['.pdf', '.pptx']):
            logger.error(f"Invalid file extension in URL: {url}")
            return {
                'success': False,
                'file_path': '',
                'filename': '',
                'error': 'URL must point to a PDF or PPTX file'
            }

        # Make request with timeout and streaming
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        logger.info(f"Content-Type: {content_type}")

        # Validate content type (allow common presentation MIME types)
        valid_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.ms-powerpoint',
            'application/octet-stream'  # Sometimes servers use generic type
        ]

        if not any(valid_type in content_type for valid_type in valid_types):
            logger.warning(f"Unexpected content type: {content_type}")

        # Save file
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, filename)

        # Write file in chunks
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        file_size = os.path.getsize(file_path)
        logger.info(f"Successfully downloaded {filename} ({file_size} bytes)")

        return {
            'success': True,
            'file_path': file_path,
            'filename': filename,
            'error': ''
        }

    except requests.exceptions.Timeout:
        logger.error(f"Timeout downloading from URL: {url}")
        return {
            'success': False,
            'file_path': '',
            'filename': '',
            'error': 'Request timed out. The URL may be too slow or unreachable.'
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading from URL: {str(e)}")
        return {
            'success': False,
            'file_path': '',
            'filename': '',
            'error': f'Failed to download file: {str(e)}'
        }

    except Exception as e:
        logger.error(f"Unexpected error downloading file: {str(e)}")
        return {
            'success': False,
            'file_path': '',
            'filename': '',
            'error': f'Unexpected error: {str(e)}'
        }
