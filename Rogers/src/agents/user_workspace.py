"""User workspace manager — per-user agents.md, soul.md, and session storage."""
from __future__ import annotations

import shutil
from pathlib import Path


_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent / "config" / "workspace"
_TEMPLATE_DIR = _WORKSPACE_ROOT / "templates"
_USERS_DIR = _WORKSPACE_ROOT / "users"


def get_user_workspace(user_id: int | str) -> Path:
    """Return the workspace directory for a given user."""
    return _USERS_DIR / str(user_id)


def get_user_sessions_dir(user_id: int | str) -> Path:
    """Return the sessions directory for a given user."""
    return get_user_workspace(user_id) / "sessions"


def ensure_user_workspace(user_id: int | str) -> Path:
    """Create the user workspace and copy templates if this is first use.

    Returns the user workspace path. Safe to call concurrently — template
    copy is idempotent.
    """
    user_dir = get_user_workspace(user_id)
    if user_dir.exists():
        return user_dir

    user_dir.mkdir(parents=True, exist_ok=True)

    # Copy template files (agents.md, soul.md)
    if _TEMPLATE_DIR.exists():
        for template_file in _TEMPLATE_DIR.iterdir():
            if template_file.is_file() and template_file.suffix == ".md":
                shutil.copy2(template_file, user_dir / template_file.name)

    # Create sessions directory
    get_user_sessions_dir(user_id).mkdir(parents=True, exist_ok=True)

    return user_dir


def load_user_sys_prompt(user_id: int | str) -> str:
    """Build the full system prompt by reading agents.md and soul.md.

    Concatenates agents.md (primary instructions) and soul.md (personality)
    with a separator. Returns empty string if neither file exists.
    """
    user_dir = get_user_workspace(user_id)
    parts = []

    agents_md = user_dir / "agents.md"
    if agents_md.exists():
        parts.append(agents_md.read_text(encoding="utf-8"))

    soul_md = user_dir / "soul.md"
    if soul_md.exists():
        parts.append(f"\n--- 性格 ---\n{soul_md.read_text(encoding='utf-8')}")

    return "\n\n".join(parts)
