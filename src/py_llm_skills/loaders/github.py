from pathlib import Path
import yaml
import re
from typing import TYPE_CHECKING
from ..exceptions import InvalidSkillError
from .base import BaseSkillLoader

if TYPE_CHECKING:
    from ..core import Skill

class GitHubSkillLoader(BaseSkillLoader):
    """
    Loads skills from .github/skills/*.md
    Very similar to Cursor loader, single markdown file with frontmatter.
    """

    def can_load(self, path: Path) -> bool:
        # We only really want to claim generic .md files if they are in a specific directory
        # OR if explicitly asked to load. 
        # But for 'can_load(path)', if path is passed directly, we check extension.
        # However, to avoid grabbing README.md, we might check for frontmatter or specific keys?
        pass 
        # Actually, the logic in core.py will likely iterate directories and call appropriate loader.
        # But if we pass a file path:
        return path.is_file() and path.suffix == ".md"

    def load(self, path: Path) -> "Skill":
        from ..core import Skill
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            raise InvalidSkillError(f"Failed to read file {path}: {e}")

        parts = content.split("---", 2)
        metadata = {}
        instructions = content

        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1]) or {}
                instructions = parts[2].strip()
            except:
                pass

        name = metadata.get("name") or path.stem
        name = re.sub(r'[^a-z0-9\-]', '-', name.lower()).strip('-')
        description = metadata.get("description") or f"Skill from {path.name}"
        
        extra_metadata = {k:v for k,v in metadata.items() if k not in ["name", "description"]}

        return Skill(
            name=name,
            description=description,
            instructions=instructions,
            path=path.parent,
            extra_metadata=extra_metadata
        )
