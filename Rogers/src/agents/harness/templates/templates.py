"""Template management for agent harness.

Centralized management of template paths and template-related utilities.
"""
from pathlib import Path


# Template directory is located within the harness package
# __file__ is at src/agents/harness/templates/templates.py
# So parent is src/agents/harness/templates
_HARNESS_DIR = Path(__file__).parent
TEMPLATE_DIR = _HARNESS_DIR
SKILLS_TEMPLATE_DIR = TEMPLATE_DIR / "skills"


def get_template_path() -> Path:
    """Get the base template directory path."""
    return TEMPLATE_DIR


def get_skills_template_path() -> Path:
    """Get the skills template directory path."""
    return SKILLS_TEMPLATE_DIR


def get_agent_template_path() -> Path:
    """Get the default agents.md template path."""
    return TEMPLATE_DIR / "agents.md"


def get_soul_template_path() -> Path:
    """Get the default soul.md template path."""
    return TEMPLATE_DIR / "soul.md"


def template_exists() -> bool:
    """Check if the template directory exists."""
    return TEMPLATE_DIR.exists()
