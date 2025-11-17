# Presentation Intelligence Tool

Transform technical presentations into strategic pre-sales intelligence using AI-powered analysis.

## Overview

The Presentation Intelligence Tool is a Flask-based web application that analyzes conference and vendor presentations using Claude AI. It extracts actionable insights for pre-sales engineers, helping them identify opportunities to add value for clients and build trust through relevant knowledge sharing.

## Features

- Upload PDF or PPTX presentation files (up to 50MB)
- Extract text content from slides automatically
- AI-powered analysis using Claude Sonnet 4.5
- Generate comprehensive reports including:
  - Executive summaries
  - Key technical insights
  - Client value connections
  - Pre-sales opportunities
  - Intelligent follow-up questions
  - GitHub repository value analysis (when applicable)
- Download results as Markdown or PDF

## Technology Stack

- **Backend**: Python 3.9+, Flask 3.0+
- **AI Engine**: Claude Sonnet 4.5 (Anthropic API)
- **Document Processing**: PyMuPDF, python-pptx
- **Output Generation**: markdown2, WeasyPrint

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Anthropic API key ([Get one here](https://console.anthropic.com/))

### Setup Steps

1. **Clone the repository**:
```bash
git clone https://github.com/seanerama/Presentation-Intelligence-Tool.git
cd Presentation-Intelligence-Tool
```

2. **Create a virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:
```bash
cp .env.example .env
```

Edit the `.env` file and add your configuration:
```
ANTHROPIC_API_KEY=your-actual-api-key-here
FLASK_SECRET_KEY=generate-a-random-secret-key
FLASK_ENV=development
FLASK_DEBUG=True
```

Generate a secure Flask secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

5. **Run the application**:
```bash
python app.py
```

6. **Access the application**:
Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. **Open the web interface** at `http://localhost:5000`

2. **Fill in the form**:
   - Presentation Title (required)
   - Presenter Names (required)
   - GitHub Repository URL (optional) - for lab guides and code samples
   - Your Notes (required) - your observations and key takeaways
   - Upload slide deck (PDF or PPTX, max 50MB)

3. **Submit for analysis** - The tool will:
   - Extract text from your presentation
   - Analyze it using Claude AI
   - Generate comprehensive insights

4. **Review results** in the browser and download as:
   - Markdown file (.md)
   - PDF file (.pdf)

## Project Structure

```
presentation-intel/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── isnstruct.md              # Full specification document
├── utils/
│   ├── __init__.py
│   ├── document_parser.py     # PDF/PPTX extraction
│   ├── claude_analyzer.py     # Claude API integration
│   └── output_generator.py    # MD/PDF generation
├── templates/
│   ├── index.html            # Upload form
│   └── results.html          # Analysis results
├── static/
│   └── css/
│       └── style.css         # Styling
├── outputs/                  # Generated files
└── uploads/                  # Temporary upload storage
```

## Configuration

### Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `FLASK_SECRET_KEY`: Secret key for Flask sessions (required)
- `FLASK_ENV`: Environment mode (development/production)
- `FLASK_DEBUG`: Enable debug mode (True/False)
- `MAX_FILE_SIZE_MB`: Maximum upload size in MB (default: 50)
- `CLEANUP_INTERVAL_HOURS`: File cleanup interval (default: 1)

## Security Considerations

- Never commit your `.env` file to version control
- Store API keys securely
- Use a strong, random Flask secret key in production
- Consider implementing rate limiting for production use
- Review uploaded files for security concerns

## Troubleshooting

### Common Issues

**"ANTHROPIC_API_KEY not found"**
- Ensure your `.env` file exists and contains your API key
- Check that python-dotenv is installed

**"Could not extract content from presentation"**
- Verify the file is a valid PDF or PPTX
- Check that the file is not password-protected
- Ensure the file size is under 50MB

**WeasyPrint installation issues**
- WeasyPrint requires system dependencies (GTK, Pango, etc.)
- See [WeasyPrint installation docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation)

## Development

### Running Tests
```bash
# Add test commands here when tests are implemented
```

### Contributing
Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions:
- GitHub Issues: [Report a bug](https://github.com/seanerama/Presentation-Intelligence-Tool/issues)
- Documentation: See `isnstruct.md` for full specification

## Credits

- Built with [Flask](https://flask.palletsprojects.com/)
- Powered by [Claude AI](https://www.anthropic.com/) (Anthropic)
- Document processing: [PyMuPDF](https://pymupdf.readthedocs.io/), [python-pptx](https://python-pptx.readthedocs.io/)

---

**Version**: 1.0 (MVP)
**Last Updated**: 2025
