"""
AI Analyzer Module
Interacts with AI providers to analyze presentation content.
Supports multiple providers: Anthropic, OpenAI, Google, Ollama, xAI.
"""

import os
from utils.ai_client import AIClient
from utils.prompt_loader import load_prompt_template, build_prompt_from_template
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_fallback_prompt(title: str, presenters: str, user_notes: str,
                          slide_content: str, github_url: Optional[str] = None,
                          additional_resources: Optional[list] = None) -> str:
    """
    Construct a generic fallback prompt when no template is available.

    This function is used when the requested prompt template cannot be loaded.
    It provides a basic technical analysis structure that works for any role.

    Args:
        title: Presentation title
        presenters: Presenter names
        user_notes: User's personal notes
        slide_content: Extracted text from slides
        github_url: Optional GitHub repository URL
        additional_resources: Optional list of fetched web resources

    Returns:
        Formatted prompt string
    """
    github_section = ""
    if github_url:
        github_section = f"- GitHub Repository: {github_url} (contains lab guides, code samples, and related materials)\n"

    # Build additional resources section
    resources_section = ""
    if additional_resources:
        resources_section = "\n\nADDITIONAL RESOURCES PROVIDED:\n"
        for i, resource in enumerate(additional_resources, 1):
            resources_section += f"\n--- Resource {i}: {resource['title']} ---\n"
            resources_section += f"URL: {resource['url']}\n"
            resources_section += f"Content:\n{resource['content']}\n"

    # Determine if we have slide content
    has_slides = slide_content and slide_content.strip()
    content_type = "presentation" if has_slides else "technical content"

    prompt = f"""You are a technical advisor analyzing {content_type}.

CONTEXT:
- Title: {title}
- {"Presenters" if has_slides else "Authors/Sources"}: {presenters}
- Attendee's Personal Notes: {user_notes}
{github_section}
{"SLIDE CONTENT EXTRACTED:" if has_slides else ""}
{slide_content if has_slides else ""}{resources_section}

YOUR TASK:
Analyze this {content_type}{"and the provided resources" if additional_resources else ""} and provide comprehensive technical insights.{" Focus on the information provided in the resource URLs since no slide deck was provided." if not has_slides and additional_resources else " Consider how the additional resources (lab guides, documentation, articles, etc.) complement and expand upon the presentation content." if additional_resources else ""}

Please structure your response in the following sections:

## EXECUTIVE SUMMARY
Provide a 3-5 sentence overview of the key value and relevance of this content.

## KEY TECHNICAL INSIGHTS
List 5-8 important technical concepts, technologies, or methodologies discussed:
- [Insight 1]
- [Insight 2]
...

{"## GITHUB REPOSITORY VALUE" if github_url else ""}
{"Analyze how the lab guides and code samples enhance the content:" if github_url else ""}
{"- What practical value do the labs/code provide?" if github_url else ""}
{"- How can these resources be used for hands-on learning?" if github_url else ""}

## PRACTICAL APPLICATIONS

### Use Cases
Explain 2-3 specific ways this information can be applied in real-world scenarios.

### Implementation Considerations
Describe key factors to consider when implementing these concepts.

### Potential Challenges
List 2-3 common challenges and how to address them.

## DEEP DIVE TOPICS
Identify 3-5 areas that warrant further exploration or research.

## FOLLOW-UP QUESTIONS
List 5-7 questions that will help deepen understanding of the topic:
1. [Question 1]
2. [Question 2]
...

Keep your response practical, technically accurate, and actionable."""

    return prompt


def analyze_presentation(title: str, presenters: str, user_notes: str,
                        slide_content: str, github_url: Optional[str] = None,
                        additional_resources: Optional[list] = None,
                        prompt_template: str = 'presales_engineer') -> Dict[str, any]:
    """
    Send content to AI provider and return analysis response.

    Uses the configured AI provider (set via AI_PROVIDER environment variable)
    to analyze presentation content using the specified prompt template.

    Args:
        title: Presentation title
        presenters: Presenter names
        user_notes: User's personal notes
        slide_content: Extracted text from slides
        github_url: Optional GitHub repository URL
        additional_resources: Optional list of fetched web resources
        prompt_template: Analysis perspective template ID (default: presales_engineer)

    Returns:
        {
            'success': bool,
            'raw_response': str,  # Full AI response
            'provider': str,      # AI provider used (anthropic, openai, etc.)
            'model': str,         # Model name used
            'error': str          # Error message if success is False
        }
    """
    try:
        # Initialize AI client (uses provider from environment)
        ai_provider = os.getenv('AI_PROVIDER')
        logger.info(f"Using AI provider: {ai_provider}")
        client = AIClient(provider=ai_provider)

        # Load and build prompt from template
        template = load_prompt_template(prompt_template)
        if not template:
            logger.warning(f"Prompt template '{prompt_template}' not found, using generic fallback prompt")
            prompt = build_fallback_prompt(title, presenters, user_notes, slide_content, github_url, additional_resources)
        else:
            logger.info(f"Using prompt template: {template.get('name', prompt_template)}")
            prompt = build_prompt_from_template(
                template, title, presenters, user_notes, slide_content, github_url, additional_resources
            )

        # Call AI API
        logger.info(f"Sending request to {ai_provider} API...")
        response = client.generate(prompt, max_tokens=4096, temperature=0.7)

        if not response['success']:
            raise Exception(response['error'])

        # Extract response
        raw_response = response['text']
        logger.info(f"Successfully received response from {ai_provider} ({response['model']})")

        # Parse the response (simple parsing - could be enhanced)
        result = {
            'raw_response': raw_response,
            'success': True,
            'provider': response['provider'],
            'model': response['model']
        }

        return result

    except Exception as e:
        logger.error(f"Error analyzing presentation with AI: {str(e)}")
        return {
            'raw_response': '',
            'success': False,
            'error': str(e)
        }
