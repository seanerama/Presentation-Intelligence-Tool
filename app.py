"""
Presentation Intelligence Tool
Flask web application for analyzing conference presentations.
"""

import os
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
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
ALLOWED_DECK_EXTENSIONS = {'pdf', 'pptx'}
ALLOWED_TRANSCRIPT_EXTENSIONS = {'txt', 'vtt'}
ALLOWED_EXTENSIONS = ALLOWED_DECK_EXTENSIONS | ALLOWED_TRANSCRIPT_EXTENSIONS


def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_deck_file(filename):
    """Check if file has allowed deck extension (PDF, PPTX)."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_DECK_EXTENSIONS


def allowed_transcript_file(filename):
    """Check if file has allowed transcript extension (TXT, VTT)."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_TRANSCRIPT_EXTENSIONS


@app.route('/', methods=['GET'])
def index():
    """Display upload form."""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Process uploaded presentation and/or transcript:
    1. Validate form inputs
    2. Save uploaded files temporarily
    3. Extract content from files
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

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        files_to_cleanup = []

        # Process slide deck
        deck_source = request.form.get('deck_source', 'none')
        slide_content = ""

        if deck_source == 'upload':
            # Handle deck file upload
            if 'deck' in request.files:
                deck_file = request.files['deck']
                if deck_file.filename != '':
                    if not allowed_deck_file(deck_file.filename):
                        flash('Invalid deck file type. Only PDF and PPTX files are supported.', 'error')
                        return redirect(url_for('index'))

                    # Save deck file
                    filename = secure_filename(deck_file.filename)
                    file_ext = filename.rsplit('.', 1)[1].lower()
                    temp_filename = f"{timestamp}_deck_{filename}"
                    deck_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)

                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    deck_file.save(deck_path)
                    files_to_cleanup.append(deck_path)
                    logger.info(f"Deck file saved: {deck_path}")

                    # Extract content from deck
                    logger.info("Extracting content from slide deck...")
                    extracted = extract_content(deck_path, file_ext)

                    if 'error' in extracted:
                        for f in files_to_cleanup:
                            if os.path.exists(f):
                                os.remove(f)
                        flash(f'Could not extract content from slide deck: {extracted.get("error")}', 'error')
                        return redirect(url_for('index'))

                    if not extracted.get('text'):
                        for f in files_to_cleanup:
                            if os.path.exists(f):
                                os.remove(f)
                        flash('No text could be extracted from the slide deck. The file may be image-based or empty.', 'error')
                        return redirect(url_for('index'))

                    slide_content = extracted['text']
                    logger.info(f"Extracted {len(slide_content)} characters from slide deck")

        elif deck_source == 'url':
            # Handle deck URL import
            deck_url = request.form.get('deck_url', '').strip()
            if deck_url:
                logger.info(f"Downloading slide deck from URL: {deck_url}")
                download_result = download_file_from_url(deck_url, app.config['UPLOAD_FOLDER'])

                if not download_result['success']:
                    flash(f"Failed to download slide deck from URL: {download_result['error']}", 'error')
                    return redirect(url_for('index'))

                deck_path = download_result['file_path']
                files_to_cleanup.append(deck_path)
                filename = download_result['filename']
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

                if not file_ext or file_ext not in ALLOWED_DECK_EXTENSIONS:
                    for f in files_to_cleanup:
                        if os.path.exists(f):
                            os.remove(f)
                    flash('Invalid file type from URL. Only PDF and PPTX files are supported.', 'error')
                    return redirect(url_for('index'))

                # Extract content from deck
                logger.info("Extracting content from downloaded slide deck...")
                extracted = extract_content(deck_path, file_ext)

                if 'error' in extracted or not extracted.get('text'):
                    for f in files_to_cleanup:
                        if os.path.exists(f):
                            os.remove(f)
                    flash('Could not extract content from the downloaded slide deck.', 'error')
                    return redirect(url_for('index'))

                slide_content = extracted['text']
                logger.info(f"Extracted {len(slide_content)} characters from downloaded deck")

        # Process transcript
        transcript_source = request.form.get('transcript_source', 'none')
        transcript_content = ""

        if transcript_source == 'upload':
            # Handle transcript file upload
            if 'transcript' in request.files:
                transcript_file = request.files['transcript']
                if transcript_file.filename != '':
                    if not allowed_transcript_file(transcript_file.filename):
                        for f in files_to_cleanup:
                            if os.path.exists(f):
                                os.remove(f)
                        flash('Invalid transcript file type. Only TXT and VTT files are supported.', 'error')
                        return redirect(url_for('index'))

                    # Save transcript file
                    filename = secure_filename(transcript_file.filename)
                    file_ext = filename.rsplit('.', 1)[1].lower()
                    temp_filename = f"{timestamp}_transcript_{filename}"
                    transcript_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)

                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    transcript_file.save(transcript_path)
                    files_to_cleanup.append(transcript_path)
                    logger.info(f"Transcript file saved: {transcript_path}")

                    # Extract content from transcript
                    logger.info("Extracting content from transcript...")
                    extracted = extract_content(transcript_path, file_ext)

                    if 'error' in extracted:
                        for f in files_to_cleanup:
                            if os.path.exists(f):
                                os.remove(f)
                        flash(f'Could not extract content from transcript: {extracted.get("error")}', 'error')
                        return redirect(url_for('index'))

                    if not extracted.get('text'):
                        for f in files_to_cleanup:
                            if os.path.exists(f):
                                os.remove(f)
                        flash('No text could be extracted from the transcript.', 'error')
                        return redirect(url_for('index'))

                    transcript_content = extracted['text']
                    logger.info(f"Extracted {len(transcript_content)} characters from transcript")

        elif transcript_source == 'url':
            # Handle transcript URL import
            transcript_url = request.form.get('transcript_url', '').strip()
            if transcript_url:
                logger.info(f"Downloading transcript from URL: {transcript_url}")
                download_result = download_file_from_url(transcript_url, app.config['UPLOAD_FOLDER'])

                if not download_result['success']:
                    for f in files_to_cleanup:
                        if os.path.exists(f):
                            os.remove(f)
                    flash(f"Failed to download transcript from URL: {download_result['error']}", 'error')
                    return redirect(url_for('index'))

                transcript_path = download_result['file_path']
                files_to_cleanup.append(transcript_path)
                filename = download_result['filename']
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

                if not file_ext or file_ext not in ALLOWED_TRANSCRIPT_EXTENSIONS:
                    for f in files_to_cleanup:
                        if os.path.exists(f):
                            os.remove(f)
                    flash('Invalid file type from URL. Only TXT and VTT files are supported for transcripts.', 'error')
                    return redirect(url_for('index'))

                # Extract content from transcript
                logger.info("Extracting content from downloaded transcript...")
                extracted = extract_content(transcript_path, file_ext)

                if 'error' in extracted or not extracted.get('text'):
                    for f in files_to_cleanup:
                        if os.path.exists(f):
                            os.remove(f)
                    flash('Could not extract content from the downloaded transcript.', 'error')
                    return redirect(url_for('index'))

                transcript_content = extracted['text']
                logger.info(f"Extracted {len(transcript_content)} characters from downloaded transcript")

        # Combine slide and transcript content
        combined_content_parts = []
        if slide_content:
            combined_content_parts.append(f"=== SLIDE DECK CONTENT ===\n\n{slide_content}")
        if transcript_content:
            combined_content_parts.append(f"=== PRESENTATION TRANSCRIPT ===\n\n{transcript_content}")

        slide_content = "\n\n".join(combined_content_parts) if combined_content_parts else ""

        # Validate we have at least one content source
        if not slide_content and not resource_urls:
            for f in files_to_cleanup:
                if os.path.exists(f):
                    os.remove(f)
            flash('Please provide at least one content source: slide deck, transcript, or resource URLs.', 'error')
            return redirect(url_for('index'))

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

        # Analyze with AI
        logger.info("Analyzing presentation with AI...")
        analysis = analyze_presentation(
            title=title,
            presenters=presenters,
            user_notes=user_notes,
            slide_content=slide_content,
            github_url=github_url if github_url else None,
            additional_resources=fetched_resources,
            prompt_template=prompt_template
        )

        if not analysis.get('success'):
            error_msg = analysis.get('error', 'Unknown error')
            flash(f'Analysis failed: {error_msg}', 'error')
            # Clean up uploaded files
            for f in files_to_cleanup:
                if os.path.exists(f):
                    os.remove(f)
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
            # Clean up uploaded files
            for f in files_to_cleanup:
                if os.path.exists(f):
                    os.remove(f)
            return redirect(url_for('index'))

        # Clean up uploaded files
        for f in files_to_cleanup:
            if os.path.exists(f):
                os.remove(f)
        if files_to_cleanup:
            logger.info(f"Cleaned up {len(files_to_cleanup)} temporary file(s)")

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


@app.route('/api/v1/prompts', methods=['GET'])
def api_get_prompts():
    """
    API endpoint to get list of available prompt templates.

    Returns:
        JSON: List of available prompt templates
    """
    try:
        from utils.prompt_loader import get_available_prompts
        prompts = get_available_prompts()
        return jsonify({
            'success': True,
            'prompts': prompts
        }), 200
    except Exception as e:
        logger.error(f"Error getting prompts: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v1/analyze', methods=['POST'])
def api_analyze():
    """
    API endpoint for presentation analysis without file uploads.

    Request JSON:
        {
            "title": "Presentation Title",
            "presenters": "Presenter Names",
            "notes": "Your analysis notes",
            "github_url": "https://github.com/..." (optional),
            "resource_urls": ["https://...", "https://..."] (optional),
            "prompt_template": "presales_engineer" (optional, default: presales_engineer)
        }

    Returns:
        JSON: Analysis results with metadata
    """
    try:
        # Parse JSON request
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400

        data = request.get_json()

        # Validate required fields
        title = data.get('title', '').strip()
        presenters = data.get('presenters', '').strip()
        user_notes = data.get('notes', '').strip()

        if not title:
            return jsonify({
                'success': False,
                'error': 'Missing required field: title'
            }), 400

        if not presenters:
            return jsonify({
                'success': False,
                'error': 'Missing required field: presenters'
            }), 400

        if not user_notes:
            return jsonify({
                'success': False,
                'error': 'Missing required field: notes'
            }), 400

        # Optional fields
        github_url = data.get('github_url', '').strip() or None
        resource_urls = data.get('resource_urls', [])
        prompt_template = data.get('prompt_template', 'presales_engineer').strip()

        # Validate resource_urls is a list
        if not isinstance(resource_urls, list):
            return jsonify({
                'success': False,
                'error': 'resource_urls must be an array of URLs'
            }), 400

        # Must have at least resource URLs since file upload not supported
        if not resource_urls:
            return jsonify({
                'success': False,
                'error': 'At least one resource URL is required for API analysis (file uploads not supported via API)'
            }), 400

        # Fetch resources from URLs
        logger.info(f"API request: Fetching content from {len(resource_urls)} resource URLs...")
        fetch_result = fetch_multiple_urls(resource_urls)

        if not fetch_result['success'] or not fetch_result['resources']:
            return jsonify({
                'success': False,
                'error': 'Could not fetch any of the provided resource URLs',
                'failed_urls': fetch_result.get('failed_urls', resource_urls)
            }), 400

        fetched_resources = fetch_result['resources']
        logger.info(f"Successfully fetched {len(fetched_resources)} resources for API analysis")

        # No slide content for API (file upload not supported)
        slide_content = ""

        # Analyze with AI
        logger.info("API request: Analyzing with AI...")
        analysis = analyze_presentation(
            title=title,
            presenters=presenters,
            user_notes=user_notes,
            slide_content=slide_content,
            github_url=github_url,
            additional_resources=fetched_resources,
            prompt_template=prompt_template
        )

        if not analysis.get('success'):
            error_msg = analysis.get('error', 'Unknown error')
            return jsonify({
                'success': False,
                'error': f'Analysis failed: {error_msg}'
            }), 500

        # Return analysis results with metadata
        response_data = {
            'success': True,
            'analysis': analysis['raw_response'],
            'metadata': {
                'title': title,
                'presenters': presenters,
                'date': datetime.now().strftime('%B %d, %Y'),
                'time': datetime.now().strftime('%I:%M %p'),
                'github_url': github_url or '',
                'prompt_template': prompt_template,
                'resources_fetched': len(fetched_resources)
            }
        }

        # Include warnings about failed URLs if any
        if fetch_result.get('failed_urls'):
            response_data['warnings'] = {
                'failed_urls': fetch_result['failed_urls'],
                'message': f"Could not fetch {len(fetch_result['failed_urls'])} URLs"
            }

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Legacy endpoint for backwards compatibility
@app.route('/api/prompts')
def get_prompts():
    """Legacy endpoint - redirects to /api/v1/prompts."""
    from utils.prompt_loader import get_available_prompts
    return {'prompts': get_available_prompts()}


if __name__ == '__main__':
    # Create required directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

    # Run the app
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
