from pathlib import Path
from typing import Dict, List, TYPE_CHECKING
import yaml
from ..exceptions import InvalidSkillError, SecurityError
from ..utils import safe_read_file
from .base import BaseSkillLoader

if TYPE_CHECKING:
    from ..core import Skill

class ClaudeSkillLoader(BaseSkillLoader):
    """
    Loads skills from directories containing a SKILL.md file.
    This is the original/standard format for py-llm-skills and Anthropic skills.
    """

    def can_load(self, path: Path) -> bool:
        """
        Returns True if:
        1. path is a directory AND contains SKILL.md
        2. OR path is a file named SKILL.md
        """
        if path.is_dir():
            return (path / "SKILL.md").exists()
        if path.is_file():
            return path.name == "SKILL.md"
        return False

    def load(self, path: Path) -> "Skill":
        from ..core import Skill
        
        # Ensure we are working with the directory
        if path.is_file():
            skill_dir = path.parent
        else:
            skill_dir = path
        
        # Use valid existing logic from core.Skill (we will move it here or import it)
        # For now, let's duplicate the logic to decouple and then clean up core.py
        
        skill_file = skill_dir / "SKILL.md"
        content = safe_read_file("SKILL.md", skill_dir)

        try:
            parts = content.split("---", 2)
            if len(parts) < 3:
                # If no frontmatter, treat whole file as instructions (fallback?) 
                # Or raise error as per spec
                raise InvalidSkillError(f"SKILL.md in {skill_dir} is missing YAML frontmatter.")

            frontmatter_str = parts[1]
            instructions = parts[2].strip()

            metadata = yaml.safe_load(frontmatter_str)
            if not isinstance(metadata, dict):
                raise InvalidSkillError(f"Invalid YAML metadata in {skill_file}")

            # Pop known fields
            input_schema = metadata.pop("input_schema", None) or {}
            
            # If input_schema is empty, provide default QueryInput schema
            # We need to import QueryInput from core, but circular imports might be tricky.
            # Let's import inside method if needed or assume Skill class handles defaults?
            # Actually Skill Pydantic model handles defaults, so passing None/Empty is fine if allowed.
            
            known_keys = {"name", "description", "version", "author", "license"}
            known = {k: metadata.pop(k) for k in list(metadata) if k in known_keys}
            extra_metadata = metadata

            resources = self._discover_resources(skill_dir)

            return Skill(
                name=known.get("name"),
                description=known.get("description"),
                version=known.get("version", "0.1.0"),
                author=known.get("author"),
                license=known.get("license"),
                instructions=instructions,
                input_schema=input_schema, # Skill model has default factory for this
                resources=resources,
                extra_metadata=extra_metadata,
                path=skill_dir,
            )

        except yaml.YAMLError as e:
            raise InvalidSkillError(f"YAML parsing error in {skill_file}: {e}")
        
    def _discover_resources(self, skill_dir: Path) -> Dict[str, List[str]]:
        """
        Same Logic as Skill._discover_resources
        """
        # We can duplicate or refactor. duplicating for isolation for now.
        resources: Dict[str, List[str]] = {}
        _SKIP_PATTERNS = {".git", "__pycache__", ".DS_Store", "node_modules"}

        for item in sorted(skill_dir.rglob("*")):
            if any(part in _SKIP_PATTERNS for part in item.parts):
                continue
            if item.is_dir():
                continue
            rel = item.relative_to(skill_dir)
            rel_str = str(rel)

            if rel_str == "SKILL.md":
                continue

            suffix = item.suffix.lower()
            name_lower = item.stem.lower()

            if suffix in {".py", ".sh", ".bash"}:
                category = "scripts"
            elif "example" in name_lower:
                category = "examples"
            elif suffix == ".md":
                category = "references"
            else:
                category = "data"

            resources.setdefault(category, []).append(rel_str)

        return resources
