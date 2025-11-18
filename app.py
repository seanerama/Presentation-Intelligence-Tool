"""
Presentation Intelligence Tool
Flask web application for analyzing conference presentations.
"""

import os
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime
import logging

from utils.document_parser import extract_content
from utils.ai_analyzer import analyze_presentation
from utils.output_generator import create_outputs
from utils.url_downloader import download_file_from_url
from utils.web_scraper import fetch_multiple_urls

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_FILE_SIZE_MB', 50)) * 1024 * 1024  # 50MB default
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'pptx'}


def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def index():
    """Display upload form."""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Process uploaded presentation:
    1. Validate form inputs
    2. Save uploaded file temporarily
    3. Extract content from file
    4. Send to AI for analysis
    5. Generate output files
    6. Render results page with download links
    """
    try:
        # Validate form inputs
        title = request.form.get('title', '').strip()
        presenters = request.form.get('presenters', '').strip()
        user_notes = request.form.get('notes', '').strip()
        github_url = request.form.get('github_url', '').strip()
        resource_urls_text = request.form.get('resource_urls', '').strip()
        prompt_template = request.form.get('prompt_template', 'presales_engineer').strip()

        if not title or not presenters or not user_notes:
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('index'))

        # Parse resource URLs (one per line)
        resource_urls = []
        if resource_urls_text:
            resource_urls = [url.strip() for url in resource_urls_text.split('\n') if url.strip()]
            logger.info(f"Found {len(resource_urls)} resource URLs to fetch")

        # Check deck source (upload, URL, or none)
        deck_source = request.form.get('deck_source', 'upload')
        file_path = None
        file_ext = None
        slide_content = None
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if deck_source == 'none':
            # No deck provided - must have resource URLs
            if not resource_urls:
                flash('Please provide either a slide deck or additional resource URLs to analyze.', 'error')
                return redirect(url_for('index'))
            logger.info("No slide deck provided - analyzing resource URLs only")
            slide_content = ""  # Empty slide content

        elif deck_source == 'url':
            # Handle URL import
            deck_url = request.form.get('deck_url', '').strip()

            if not deck_url:
                flash('Please provide a URL to the presentation file.', 'error')
                return redirect(url_for('index'))

            logger.info(f"Downloading presentation from URL: {deck_url}")

            # Download file from URL
            download_result = download_file_from_url(deck_url, app.config['UPLOAD_FOLDER'])

            if not download_result['success']:
                flash(f"Failed to download file from URL: {download_result['error']}", 'error')
                return redirect(url_for('index'))

            file_path = download_result['file_path']
            filename = download_result['filename']
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

            if not file_ext or file_ext not in ALLOWED_EXTENSIONS:
                # Clean up downloaded file
                if os.path.exists(file_path):
                    os.remove(file_path)
                flash('Invalid file type. Only PDF and PPTX files are supported.', 'error')
                return redirect(url_for('index'))

            logger.info(f"File downloaded: {file_path}")

        else:
            # Handle file upload
            if 'deck' not in request.files:
                flash('No file uploaded.', 'error')
                return redirect(url_for('index'))

            file = request.files['deck']

            if file.filename == '':
                flash('No file selected.', 'error')
                return redirect(url_for('index'))

            if not allowed_file(file.filename):
                flash('Invalid file type. Only PDF and PPTX files are supported.', 'error')
                return redirect(url_for('index'))

            # Save uploaded file
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()
            temp_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)

            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(file_path)
            logger.info(f"File saved: {file_path}")

        # Extract content from file if we have one
        if deck_source != 'none' and file_path:
            logger.info("Extracting content from presentation...")
            extracted = extract_content(file_path, file_ext)

            if 'error' in extracted:
                error_msg = extracted.get('error', 'Unknown error')
                logger.error(f"Extraction error: {error_msg}")
                flash(f'Could not extract content from presentation: {error_msg}', 'error')
                # Clean up uploaded file
                if os.path.exists(file_path):
                    os.remove(file_path)
                return redirect(url_for('index'))

            if not extracted.get('text'):
                logger.warning(f"No text extracted. Pages/Slides: {extracted.get('pages', extracted.get('slides', 0))}, Has images: {extracted.get('has_images', False)}")
                flash('No text could be extracted from the presentation. The file may be image-based (scanned slides) or empty.', 'error')
                # Clean up uploaded file
                if os.path.exists(file_path):
                    os.remove(file_path)
                return redirect(url_for('index'))

            slide_content = extracted['text']
            logger.info(f"Extracted {len(slide_content)} characters of text")

        # Fetch additional resources if URLs provided
        fetched_resources = None
        if resource_urls:
            logger.info(f"Fetching content from {len(resource_urls)} additional resource URLs...")
            fetch_result = fetch_multiple_urls(resource_urls)
            if fetch_result['success']:
                fetched_resources = fetch_result['resources']
                logger.info(f"Successfully fetched {len(fetched_resources)} resources")
                if fetch_result['failed_urls']:
                    flash(f"Warning: Could not fetch {len(fetch_result['failed_urls'])} URLs", 'warning')
            else:
                flash("Warning: Could not fetch any of the provided resource URLs", 'warning')

        # Analyze with Claude
        logger.info("Analyzing presentation with AI...")
        analysis = analyze_presentation(
            title=title,
            presenters=presenters,
            user_notes=user_notes,
            slide_content=slide_content,
            github_url=github_url if github_url else None,
            additional_resources=fetched_resources
        , prompt_template=prompt_template)

        if not analysis.get('success'):
            error_msg = analysis.get('error', 'Unknown error')
            flash(f'Analysis failed: {error_msg}', 'error')
            # Clean up uploaded file if one exists
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            return redirect(url_for('index'))

        # Generate output files
        logger.info("Generating output files...")
        metadata = {
            'title': title,
            'presenters': presenters,
            'date': datetime.now().strftime('%B %d, %Y'),
            'time': datetime.now().strftime('%I:%M %p'),
            'github_url': github_url if github_url else ''
        }

        base_filename = f"analysis_{timestamp}"
        outputs = create_outputs(
            analysis=analysis,
            metadata=metadata,
            output_dir=app.config['OUTPUT_FOLDER'],
            base_filename=base_filename
        )

        if not outputs.get('success'):
            flash('Failed to generate output files.', 'error')
            # Clean up uploaded file if one exists
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            return redirect(url_for('index'))

        # Clean up uploaded file if one exists
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")

        # Render results page
        return render_template(
            'results.html',
            analysis=analysis['raw_response'],
            metadata=metadata,
            markdown_filename=os.path.basename(outputs['markdown_path']),
            pdf_filename=os.path.basename(outputs['pdf_path'])
        )

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/download/<file_type>/<filename>')
def download(file_type, filename):
    """
    Serve generated files for download.

    Args:
        file_type: 'md' or 'pdf'
        filename: Generated filename
    """
    try:
        # Secure the filename
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)

        if not os.path.exists(file_path):
            flash('File not found.', 'error')
            return redirect(url_for('index'))

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        flash('Error downloading file.', 'error')
        return redirect(url_for('index'))


@app.route('/health')
def health():
    """Health check endpoint."""
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}


if __name__ == '__main__':
    # Create required directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

    # Run the app
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)


@app.route('/api/prompts')
def get_prompts():
    """Get list of available prompt templates."""
    from utils.prompt_loader import get_available_prompts
    return {'prompts': get_available_prompts()}
