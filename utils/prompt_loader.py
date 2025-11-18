"""
Prompt Loader Module
Loads and manages prompt templates for different analysis perspectives.
"""

import os
import json
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompts')


def get_available_prompts() -> List[Dict[str, str]]:
    """
    Get list of available prompt templates.

    Returns:
        List of dicts with prompt metadata: [{'id': 'presales_engineer', 'name': 'Pre-Sales Engineer', 'description': '...'}]
    """
    prompts = []

    try:
        if not os.path.exists(PROMPTS_DIR):
            logger.warning(f"Prompts directory not found: {PROMPTS_DIR}")
            return prompts

        for filename in os.listdir(PROMPTS_DIR):
            if filename.endswith('.json'):
                prompt_id = filename.replace('.json', '')
                filepath = os.path.join(PROMPTS_DIR, filename)

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        template = json.load(f)
                        prompts.append({
                            'id': prompt_id,
                            'name': template.get('name', prompt_id),
                            'description': template.get('description', '')
                        })
                except Exception as e:
                    logger.error(f"Error loading prompt {filename}: {str(e)}")

        return sorted(prompts, key=lambda x: x['name'])

    except Exception as e:
        logger.error(f"Error listing prompts: {str(e)}")
        return prompts


def load_prompt_template(prompt_id: str) -> Optional[Dict]:
    """
    Load a specific prompt template.

    Args:
        prompt_id: ID of the prompt template (filename without .json)

    Returns:
        Prompt template dict or None if not found
    """
    try:
        filepath = os.path.join(PROMPTS_DIR, f"{prompt_id}.json")

        if not os.path.exists(filepath):
            logger.error(f"Prompt template not found: {filepath}")
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            template = json.load(f)
            logger.info(f"Loaded prompt template: {template.get('name', prompt_id)}")
            return template

    except Exception as e:
        logger.error(f"Error loading prompt template {prompt_id}: {str(e)}")
        return None


def build_section(section: Dict, indent: int = 0) -> str:
    """Build a section of the prompt from template."""
    lines = []
    prefix = "" if indent == 0 else "#" * indent + " "

    # Add section title
    if 'title' in section:
        lines.append(f"\n{prefix}## {section['title']}")

    # Add instruction
    if 'instruction' in section:
        lines.append(section['instruction'])

    # Add subsections
    if 'subsections' in section:
        for subsection in section['subsections']:
            lines.append(f"\n### {subsection['title']}")
            if 'instruction' in subsection:
                lines.append(subsection['instruction'])

    return '\n'.join(lines)


def build_prompt_from_template(
    template: Dict,
    title: str,
    presenters: str,
    user_notes: str,
    slide_content: str,
    github_url: Optional[str] = None,
    additional_resources: Optional[list] = None
) -> str:
    """
    Build a complete prompt from a template with provided context.

    Args:
        template: Loaded prompt template dict
        title: Presentation/content title
        presenters: Presenter/author names
        user_notes: User's personal notes
        slide_content: Extracted slide text (can be empty)
        github_url: Optional GitHub repository URL
        additional_resources: Optional list of fetched web resources

    Returns:
        Complete formatted prompt string
    """
    # Determine content type
    has_slides = slide_content and slide_content.strip()
    content_type = "presentation" if has_slides else "technical content"

    # Build GitHub section
    github_section = ""
    if github_url:
        github_section = f"- GitHub Repository: {github_url} (contains lab guides, code samples, and related materials)\n"

    # Build resources section
    resources_section = ""
    if additional_resources:
        resources_section = "\n\nADDITIONAL RESOURCES PROVIDED:\n"
        for i, resource in enumerate(additional_resources, 1):
            resources_section += f"\n--- Resource {i}: {resource['title']} ---\n"
            resources_section += f"URL: {resource['url']}\n"
            resources_section += f"Content:\n{resource['content']}\n"

    # Build task description with replacements
    resources_note = "and the provided resources" if additional_resources else ""
    resource_focus = ""
    if not has_slides and additional_resources:
        resource_focus = " Focus on the information provided in the resource URLs since no slide deck was provided."
    elif additional_resources:
        resource_focus = " Consider how the additional resources (lab guides, documentation, articles, etc.) complement and expand upon the presentation content."

    task_description = template.get('task_description', '').format(
        content_type=content_type,
        resources_note=resources_note,
        resource_focus=resource_focus
    )

    # Build prompt header
    prompt_lines = [
        f"You are a {template.get('role', 'technical advisor')} analyzing {content_type}.",
        "",
        "CONTEXT:",
        f"- Title: {title}",
        f"- {'Presenters' if has_slides else 'Authors/Sources'}: {presenters}",
        f"- Attendee's Personal Notes: {user_notes}",
        github_section
    ]

    if has_slides:
        prompt_lines.append("SLIDE CONTENT EXTRACTED:")
        prompt_lines.append(slide_content)

    if resources_section:
        prompt_lines.append(resources_section)

    prompt_lines.append("")
    prompt_lines.append("YOUR TASK:")
    prompt_lines.append(task_description)
    prompt_lines.append("")
    prompt_lines.append("Please structure your response in the following sections:")

    # Build sections
    for section in template.get('sections', []):
        prompt_lines.append(build_section(section))

    # Add closing
    if 'closing' in template:
        prompt_lines.append("")
        prompt_lines.append(template['closing'])

    return '\n'.join(prompt_lines)
