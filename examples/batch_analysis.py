#!/usr/bin/env python3
"""
Batch Analysis Example

This script demonstrates how to analyze multiple presentations/resources
in batch using the Presentation Intelligence Tool API.
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict


API_BASE_URL = "http://localhost:5000/api/v1"
OUTPUT_DIR = Path("batch_outputs")


def analyze_content(
    title: str,
    presenters: str,
    notes: str,
    resource_urls: List[str],
    github_url: str = None,
    prompt_template: str = "presales_engineer"
) -> Dict:
    """Submit content for AI analysis."""
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
        response = requests.post(
            f"{API_BASE_URL}/analyze",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minute timeout for AI analysis
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timeout - analysis took too long'}
    except requests.exceptions.HTTPError as e:
        try:
            error_data = e.response.json()
            return {'success': False, 'error': error_data.get('error', str(e))}
        except:
            return {'success': False, 'error': str(e)}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def save_analysis(analysis: str, filename: str):
    """Save analysis to file."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    filepath = OUTPUT_DIR / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(analysis)

    return filepath


def main():
    """Process multiple presentations in batch."""

    print("Batch Analysis Example")
    print("=" * 60)
    print()

    # Define multiple presentations to analyze
    presentations = [
        {
            "title": "Introduction to Network Automation",
            "presenters": "Network Automation Team",
            "notes": "Foundational concepts in network automation using Python",
            "resource_urls": [
                "https://raw.githubusercontent.com/ktbyers/netmiko/develop/README.md"
            ],
            "github_url": "https://github.com/ktbyers/netmiko",
            "prompt_template": "network_engineer",
            "output_file": "netmiko_analysis.md"
        },
        {
            "title": "DevOps Best Practices",
            "presenters": "DevOps Guild",
            "notes": "CI/CD pipeline design and infrastructure as code",
            "resource_urls": [
                "https://raw.githubusercontent.com/ansible/ansible/devel/README.md"
            ],
            "github_url": "https://github.com/ansible/ansible",
            "prompt_template": "presales_engineer",
            "output_file": "ansible_analysis.md"
        },
        # Add more presentations as needed
    ]

    results = []
    total = len(presentations)

    print(f"Processing {total} presentation(s)...\n")

    for idx, pres in enumerate(presentations, 1):
        print(f"[{idx}/{total}] Analyzing: {pres['title']}")
        print(f"          Template: {pres['prompt_template']}")

        start_time = time.time()

        # Remove output_file from API request
        output_file = pres.pop('output_file', f"analysis_{idx}.md")
        result = analyze_content(**pres)

        elapsed = time.time() - start_time

        if result.get('success'):
            # Save analysis
            filepath = save_analysis(result['analysis'], output_file)
            print(f"          ✓ Completed in {elapsed:.1f}s")
            print(f"          Saved to: {filepath}")

            results.append({
                'title': pres['title'],
                'success': True,
                'file': str(filepath),
                'time': elapsed
            })

        else:
            print(f"          ✗ Failed: {result.get('error')}")

            results.append({
                'title': pres['title'],
                'success': False,
                'error': result.get('error'),
                'time': elapsed
            })

        print()

        # Add delay between requests to avoid overwhelming the API
        if idx < total:
            time.sleep(2)

    # Summary
    print("=" * 60)
    print("Batch Analysis Summary")
    print("=" * 60)

    successful = sum(1 for r in results if r['success'])
    failed = total - successful

    print(f"Total: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print()

    if successful > 0:
        print("Successfully analyzed:")
        for r in results:
            if r['success']:
                print(f"  ✓ {r['title']}")
                print(f"    File: {r['file']}")
                print(f"    Time: {r['time']:.1f}s")

    if failed > 0:
        print("\nFailed analyses:")
        for r in results:
            if not r['success']:
                print(f"  ✗ {r['title']}")
                print(f"    Error: {r['error']}")

    # Save summary to JSON
    summary_file = OUTPUT_DIR / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total': total,
            'successful': successful,
            'failed': failed,
            'results': results
        }, f, indent=2)

    print(f"\nSummary saved to: {summary_file}")


if __name__ == "__main__":
    main()
