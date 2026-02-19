from pathlib import Path
import yaml
import re
from typing import TYPE_CHECKING
from ..exceptions import InvalidSkillError
from ..core import QueryInput
from .base import BaseSkillLoader

if TYPE_CHECKING:
    from ..core import Skill

class CursorSkillLoader(BaseSkillLoader):
    """
    Loads skills from Cursor .mdc files.
    These are typically single markdown files with frontmatter.
    """

    def can_load(self, path: Path) -> bool:
        return path.is_file() and path.suffix == ".mdc"

    def load(self, path: Path) -> "Skill":
        from ..core import Skill
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            raise InvalidSkillError(f"Failed to read .mdc file {path}: {e}")

        # Parse frontmatter
        # .mdc files usually have YAML frontmatter
        parts = content.split("---", 2)
        
        metadata = {}
        instructions = content
        
        if len(parts) >= 3:
            try:
                frontmatter_str = parts[1]
                metadata = yaml.safe_load(frontmatter_str) or {}
                instructions = parts[2].strip()
            except yaml.YAMLError:
                # Fallback: treat entire file as instructions
                pass
        
        # Cursor rules might not have 'name' in frontmatter, so use filename
        name = metadata.get("name") or path.stem
        # Sanitize name to match our strict regex if needed, or update regex in Skill model?
        # Skill model requires: lowercase letters/numbers/hyphens
        name = re.sub(r'[^a-z0-9\-]', '-', name.lower()).strip('-')
        
        description = metadata.get("description") or f"Cursor rule from {path.name}"
        
        # Map generic metadata
        # .mdc might have "globs" field which is useful to know when to apply
        extra_metadata = {k:v for k,v in metadata.items() if k not in ["name", "description"]}
        
        return Skill(
            name=name,
            description=description,
            instructions=instructions,
            # Cursor rules usually apply to current context, explicit input schema isn't standard
            # We use default QueryInput
            # We treat the single file as the only resource?
            path=path.parent, # Skill expects a directory path usually, but for single file skills this is ambiguous.
                              # We'll point to parent dir, but "resources" will be empty.
            extra_metadata=extra_metadata
        )
