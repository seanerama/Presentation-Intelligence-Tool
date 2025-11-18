# API Usage Examples

This directory contains example scripts demonstrating how to use the Presentation Intelligence Tool REST API.

## Prerequisites

- Presentation Intelligence Tool running locally on `http://localhost:5000`
- API provider configured (see main README.md for setup)

### Python Examples
- Python 3.8+
- `requests` library: `pip install requests`

### Bash Examples
- bash shell
- `curl` (usually pre-installed)
- `jq` for JSON processing: `sudo apt install jq` or `brew install jq`

## Examples

### 1. Basic API Usage (Python)

**File:** `api_example.py`

Simple example that demonstrates:
- Getting available prompt templates
- Submitting an analysis request
- Handling responses and errors
- Saving results to file

**Usage:**
```bash
python api_example.py
```

**Output:**
- Prints analysis progress and results
- Saves analysis to `example_analysis.md`

### 2. Basic API Usage (Bash)

**File:** `api_example.sh`

Shell script equivalent of the Python example.

**Usage:**
```bash
chmod +x api_example.sh
./api_example.sh
```

**Output:**
- Prints colored output showing progress
- Saves analysis to `bash_example_analysis.md`

### 3. Batch Processing

**File:** `batch_analysis.py`

Advanced example for analyzing multiple presentations in a batch.

**Usage:**
```bash
python batch_analysis.py
```

**Features:**
- Process multiple presentations sequentially
- Save each analysis to a separate file
- Generate summary report in JSON format
- Handle errors gracefully

**Customization:**
Edit the `presentations` list in the script to add your own content:

```python
presentations = [
    {
        "title": "Your Presentation Title",
        "presenters": "Presenter Names",
        "notes": "Your notes about the content",
        "resource_urls": [
            "https://example.com/resource1",
            "https://example.com/resource2"
        ],
        "github_url": "https://github.com/user/repo",  # optional
        "prompt_template": "presales_engineer",
        "output_file": "my_analysis.md"
    },
    # Add more presentations...
]
```

**Output:**
- Individual analysis files in `batch_outputs/`
- Summary JSON in `batch_outputs/batch_summary_TIMESTAMP.json`

## Quick Start Guide

### 1. Start the Application

```bash
# In the main project directory
uv run python app.py
```

### 2. Run an Example

```bash
# Run Python example
cd examples
python api_example.py

# Or run Bash example
./api_example.sh
```

### 3. Customize for Your Needs

Modify the example scripts with your own:
- Presentation titles and presenter names
- Resource URLs (documentation, lab guides, articles)
- GitHub repository URLs
- Prompt templates (presales_engineer, network_engineer, security_analyst)
- Output file names

## API Endpoint Reference

### GET `/api/v1/prompts`

Get list of available analysis templates.

```bash
curl http://localhost:5000/api/v1/prompts
```

### POST `/api/v1/analyze`

Submit content for analysis.

```bash
curl -X POST http://localhost:5000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Workshop Title",
    "presenters": "Name(s)",
    "notes": "Your observations",
    "resource_urls": ["https://example.com/guide"],
    "prompt_template": "network_engineer"
  }'
```

## Common Use Cases

### Analyze Documentation

```python
result = analyze_content(
    title="Product Documentation Review",
    presenters="Documentation Team",
    notes="Comprehensive API documentation with examples",
    resource_urls=[
        "https://docs.example.com/api",
        "https://docs.example.com/quickstart"
    ],
    prompt_template="presales_engineer"
)
```

### Analyze GitHub Repository

```python
result = analyze_content(
    title="Open Source Tool Analysis",
    presenters="OSS Community",
    notes="Popular automation framework with active community",
    resource_urls=[
        "https://raw.githubusercontent.com/user/repo/main/README.md"
    ],
    github_url="https://github.com/user/repo",
    prompt_template="network_engineer"
)
```

### Security Review

```python
result = analyze_content(
    title="Security Advisory Review",
    presenters="Security Team",
    notes="Critical vulnerability disclosure and mitigation",
    resource_urls=[
        "https://example.com/security-advisory"
    ],
    prompt_template="security_analyst"
)
```

## Troubleshooting

### Connection Refused

**Error:** `Connection refused` or `Failed to connect`

**Solution:** Ensure the Flask app is running:
```bash
uv run python app.py
```

### JSON Decode Error

**Error:** `JSONDecodeError` or invalid response

**Solution:** Check that you're using the correct API endpoint URL and the app is healthy:
```bash
curl http://localhost:5000/health
```

### Analysis Timeout

**Error:** Request timeout after 120 seconds

**Solution:**
- Reduce number of resource URLs
- Check that resource URLs are accessible
- Ensure AI provider API is responding (check logs)

### Missing Required Field

**Error:** `Missing required field: title`

**Solution:** Ensure all required fields are present:
- `title` (string)
- `presenters` (string)
- `notes` (string)
- `resource_urls` (array with at least one URL)

## Tips

1. **Start Small**: Begin with one or two resource URLs to test
2. **Check URLs**: Ensure resource URLs are publicly accessible
3. **Use Appropriate Templates**: Match the prompt template to your analysis needs
4. **Handle Errors**: Always check the `success` field in responses
5. **Add Delays**: When batch processing, add delays between requests to avoid overwhelming the API
6. **Save Results**: Always save analysis results to files for future reference

## Further Reading

See the main [README.md](../README.md) for:
- Full API documentation
- Security considerations
- Authentication examples
- Rate limiting examples
