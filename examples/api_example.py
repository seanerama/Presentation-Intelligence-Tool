#!/usr/bin/env python3
"""
Example Python script for using the Presentation Intelligence Tool API.

This demonstrates how to:
1. Get available prompt templates
2. Submit an analysis request
3. Handle responses and errors
4. Save results to file
"""

import requests
import json
import sys
from typing import Dict, List


# Configuration
API_BASE_URL = "http://localhost:5000/api/v1"


def get_available_prompts() -> List[Dict]:
    """Get list of available analysis prompt templates."""
    try:
        response = requests.get(f"{API_BASE_URL}/prompts")
        response.raise_for_status()
        data = response.json()

        if data.get('success'):
            return data.get('prompts', [])
        else:
            print(f"Error getting prompts: {data.get('error')}")
            return []
    except Exception as e:
        print(f"Error: {str(e)}")
        return []


def analyze_content(
    title: str,
    presenters: str,
    notes: str,
    resource_urls: List[str],
    github_url: str = None,
    prompt_template: str = "presales_engineer"
) -> Dict:
    """
    Submit content for AI analysis.

    Args:
        title: Title of the content
        presenters: Names of presenters/authors
        notes: Your personal notes and observations
        resource_urls: List of URLs to fetch content from
        github_url: Optional GitHub repository URL
        prompt_template: Analysis perspective (default: presales_engineer)

    Returns:
        API response dictionary
    """
    # Prepare request payload
    payload = {
        "title": title,
        "presenters": presenters,
        "notes": notes,
        "resource_urls": resource_urls,
        "prompt_template": prompt_template
    }

    if github_url:
        payload["github_url"] = github_url

    try:
        # Send POST request
        response = requests.post(
            f"{API_BASE_URL}/analyze",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()

        return response.json()

    except requests.exceptions.HTTPError as e:
        # Try to extract error message from response
        try:
            error_data = e.response.json()
            return {
                'success': False,
                'error': error_data.get('error', str(e))
            }
        except:
            return {
                'success': False,
                'error': str(e)
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def save_analysis_to_file(analysis: str, filename: str = "analysis.md"):
    """Save analysis results to a markdown file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(analysis)
        print(f"Analysis saved to: {filename}")
    except Exception as e:
        print(f"Error saving file: {str(e)}")


def main():
    """Example usage of the API."""

    print("Presentation Intelligence Tool - API Example\n")

    # 1. Get available prompt templates
    print("1. Fetching available prompt templates...")
    prompts = get_available_prompts()

    if prompts:
        print(f"   Found {len(prompts)} templates:")
        for prompt in prompts:
            print(f"   - {prompt['id']}: {prompt['name']}")
            print(f"     {prompt['description']}")
    else:
        print("   No prompts found or API error")
        sys.exit(1)

    print()

    # 2. Submit analysis request
    print("2. Submitting analysis request...")

    # Example data
    analysis_data = {
        "title": "Network Automation with Python Workshop",
        "presenters": "John Doe, Jane Smith",
        "notes": "Excellent hands-on workshop covering Netmiko, NAPALM, and Ansible. Focus on multi-vendor network automation.",
        "resource_urls": [
            "https://raw.githubusercontent.com/ktbyers/netmiko/develop/README.md"
        ],
        "github_url": "https://github.com/ktbyers/netmiko",
        "prompt_template": "network_engineer"
    }

    print(f"   Title: {analysis_data['title']}")
    print(f"   Template: {analysis_data['prompt_template']}")
    print(f"   Resources: {len(analysis_data['resource_urls'])} URLs")

    # Submit request
    result = analyze_content(**analysis_data)

    print()

    # 3. Handle response
    if result.get('success'):
        print("3. Analysis completed successfully!")

        metadata = result.get('metadata', {})
        print(f"   Resources fetched: {metadata.get('resources_fetched', 0)}")
        print(f"   Date: {metadata.get('date')}")
        print(f"   Template used: {metadata.get('prompt_template')}")

        # Check for warnings
        if 'warnings' in result:
            warnings = result['warnings']
            print(f"\n   Warnings: {warnings.get('message')}")
            if warnings.get('failed_urls'):
                print(f"   Failed URLs: {', '.join(warnings['failed_urls'])}")

        # Save analysis to file
        print()
        analysis_text = result.get('analysis', '')
        save_analysis_to_file(analysis_text, "example_analysis.md")

        # Print first 500 characters
        print("\n   Analysis preview:")
        print("   " + "-" * 60)
        preview = analysis_text[:500].replace('\n', '\n   ')
        print(f"   {preview}...")
        print("   " + "-" * 60)

    else:
        print(f"3. Analysis failed!")
        print(f"   Error: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
