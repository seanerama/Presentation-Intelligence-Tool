"""
Web Scraper Module
Fetches and extracts content from web URLs.
"""

import requests
from typing import Dict, List
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_url_content(url: str, timeout: int = 15) -> Dict[str, any]:
    """
    Fetch and extract text content from a URL.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        {
            'success': bool,
            'url': str,
            'title': str,
            'content': str,
            'error': str
        }
    """
    try:
        logger.info(f"Fetching content from: {url}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()

        # Get title
        title = soup.title.string if soup.title else url

        # Extract text content
        text = soup.get_text(separator='\n', strip=True)

        # Clean up text (remove excessive whitespace)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        content = '\n'.join(lines)

        logger.info(f"Successfully fetched {len(content)} characters from {url}")

        return {
            'success': True,
            'url': url,
            'title': title,
            'content': content[:10000],  # Limit to 10k chars per URL
            'error': ''
        }

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching URL: {url}")
        return {
            'success': False,
            'url': url,
            'title': '',
            'content': '',
            'error': 'Request timed out'
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL {url}: {str(e)}")
        return {
            'success': False,
            'url': url,
            'title': '',
            'content': '',
            'error': f'Failed to fetch: {str(e)}'
        }

    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {str(e)}")
        return {
            'success': False,
            'url': url,
            'title': '',
            'content': '',
            'error': f'Unexpected error: {str(e)}'
        }


def fetch_multiple_urls(urls: List[str]) -> Dict[str, any]:
    """
    Fetch content from multiple URLs.

    Args:
        urls: List of URLs to fetch

    Returns:
        {
            'success': bool,
            'resources': [
                {
                    'url': str,
                    'title': str,
                    'content': str
                }
            ],
            'failed_urls': [str],
            'summary': str
        }
    """
    if not urls:
        return {
            'success': True,
            'resources': [],
            'failed_urls': [],
            'summary': ''
        }

    logger.info(f"Fetching content from {len(urls)} URLs")

    resources = []
    failed_urls = []

    for url in urls:
        result = fetch_url_content(url.strip())
        if result['success']:
            resources.append({
                'url': result['url'],
                'title': result['title'],
                'content': result['content']
            })
        else:
            failed_urls.append(url)
            logger.warning(f"Failed to fetch {url}: {result['error']}")

    # Create summary
    if resources:
        summary = f"Successfully fetched {len(resources)} resource(s)"
        if failed_urls:
            summary += f" ({len(failed_urls)} failed)"
    else:
        summary = "No resources were successfully fetched"

    logger.info(summary)

    return {
        'success': len(resources) > 0 or len(urls) == 0,
        'resources': resources,
        'failed_urls': failed_urls,
        'summary': summary
    }
