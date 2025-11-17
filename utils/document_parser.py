"""
Document Parser Module
Extracts text content from PDF and PPTX files.
"""

import fitz  # PyMuPDF
from pptx import Presentation
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_from_pdf(file_path: str) -> Dict[str, any]:
    """
    Extract text from PDF slides.

    Args:
        file_path: Path to PDF file

    Returns:
        {
            'text': str,  # All extracted text
            'pages': int,  # Number of pages
            'has_images': bool  # Whether images were detected
        }
    """
    try:
        doc = fitz.open(file_path)
        text_content = []
        has_images = False

        for page_num, page in enumerate(doc, 1):
            # Extract text from page
            page_text = page.get_text()
            if page_text.strip():
                text_content.append(f"--- Page {page_num} ---\n{page_text}")

            # Check for images (optional for MVP)
            image_list = page.get_images()
            if image_list:
                has_images = True

        doc.close()

        result = {
            'text': '\n\n'.join(text_content),
            'pages': len(doc),
            'has_images': has_images
        }

        logger.info(f"Successfully extracted text from PDF: {len(doc)} pages")
        return result

    except Exception as e:
        logger.error(f"Error extracting PDF content: {str(e)}")
        return {
            'text': '',
            'pages': 0,
            'has_images': False,
            'error': str(e)
        }


def extract_from_pptx(file_path: str) -> Dict[str, any]:
    """
    Extract text from PowerPoint slides.

    Args:
        file_path: Path to PPTX file

    Returns:
        {
            'text': str,  # All extracted text from slides
            'slides': int,  # Number of slides
            'notes': str  # Speaker notes if available
        }
    """
    try:
        prs = Presentation(file_path)
        text_content = []
        notes_content = []

        for slide_num, slide in enumerate(prs.slides, 1):
            slide_text = []

            # Extract text from shapes
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text)

            if slide_text:
                text_content.append(f"--- Slide {slide_num} ---\n" + '\n'.join(slide_text))

            # Extract speaker notes
            if slide.has_notes_slide:
                notes_frame = slide.notes_slide.notes_text_frame
                if notes_frame and notes_frame.text.strip():
                    notes_content.append(f"Notes for Slide {slide_num}: {notes_frame.text}")

        result = {
            'text': '\n\n'.join(text_content),
            'slides': len(prs.slides),
            'notes': '\n\n'.join(notes_content) if notes_content else ''
        }

        logger.info(f"Successfully extracted text from PPTX: {len(prs.slides)} slides")
        return result

    except Exception as e:
        logger.error(f"Error extracting PPTX content: {str(e)}")
        return {
            'text': '',
            'slides': 0,
            'notes': '',
            'error': str(e)
        }


def extract_content(file_path: str, file_type: str) -> Dict[str, any]:
    """
    Main entry point - routes to appropriate extractor.

    Args:
        file_path: Path to uploaded file
        file_type: 'pdf' or 'pptx'

    Returns:
        Extracted content dictionary
    """
    file_type = file_type.lower()

    if file_type == 'pdf':
        return extract_from_pdf(file_path)
    elif file_type in ['pptx', 'ppt']:
        return extract_from_pptx(file_path)
    else:
        logger.error(f"Unsupported file type: {file_type}")
        return {
            'text': '',
            'error': f'Unsupported file type: {file_type}'
        }
