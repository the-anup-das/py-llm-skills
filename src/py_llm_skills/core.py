import re
import logging
import mimetypes
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, ValidationError, field_validator
import yaml

from .utils import safe_read_file
from .exceptions import InvalidSkillError, SecurityError
# Loaders imported inside Skill.load to avoid circular dependency

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Anthropic validation constants (from skills-guide docs)
# ---------------------------------------------------------------------------
_NAME_MAX_LEN = 64
_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-]*$")
_NAME_RESERVED = {"anthropic", "claude"}
_DESCRIPTION_MAX_LEN = 1024

# Directories / files to skip when walking a skill directory
_SKIP_PATTERNS = {".git", "__pycache__", ".DS_Store", "node_modules"}


class QueryInput(BaseModel):
    """Default input schema for skills: a simple natural language query."""
    query: str = Field(..., description="The user's request or query for this skill.")


class Skill(BaseModel):
    """
    Represents an AI Agent Skill.
    """

    # -- Required metadata (Anthropic rules) ---------------------------------
    name: str = Field(
        ...,
        description="Unique name (≤64 chars, lowercase letters/numbers/hyphens).",
    )
    description: str = Field(
        ...,
        description="What the skill does and when to use it (≤1024 chars).",
    )

    # -- Optional metadata ---------------------------------------------------
    version: str = Field("0.1.0", description="Semantic version of the skill.")
    author: Optional[str] = None
    license: Optional[str] = None

    # -- Content -------------------------------------------------------------
    instructions: str = Field(
        ..., description="Body of SKILL.md (detailed instructions / system prompt)."
    )

    # -- Tool definition -----------------------------------------------------
    input_schema: Dict[str, Any] = Field(
        default_factory=lambda: QueryInput.model_json_schema(),
        description="JSON Schema for the tool input.",
    )

    # -- Companion resources discovered in the skill directory ----------------
    resources: Dict[str, List[str]] = Field(
        default_factory=dict,
        description=(
            "Map of resource category → list of relative file paths. "
            "e.g. {'scripts': ['scripts/analyze.py'], "
            "'references': ['reference.md', 'FORMS.md'], "
            "'examples': ['examples.md']}"
        ),
    )

    # -- Catch-all for extra YAML frontmatter fields -------------------------
    extra_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Any extra YAML frontmatter fields not captured above.",
    )

    # -- Internal (excluded from serialisation) ------------------------------
    path: Path = Field(..., exclude=True)

    # -----------------------------------------------------------------------
    # Validators
    # -----------------------------------------------------------------------
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v) > _NAME_MAX_LEN:
            raise ValueError(
                f"Skill name must be ≤{_NAME_MAX_LEN} chars, got {len(v)}."
            )
        if not _NAME_PATTERN.match(v):
            # Relax validation slightly for auto-generated names from filenames?
            # Or enforce it strictly. For now, strictly as per previous spec.
            raise ValueError(
                "Skill name must contain only lowercase letters, numbers, and hyphens, "
                f"and start with a letter or number. Got: '{v}'."
            )
        if v in _NAME_RESERVED:
            raise ValueError(f"Skill name '{v}' is reserved.")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Skill description must not be empty.")
        if len(v) > _DESCRIPTION_MAX_LEN:
            raise ValueError(
                f"Skill description must be ≤{_DESCRIPTION_MAX_LEN} chars, got {len(v)}."
            )
        return v

    # -----------------------------------------------------------------------
    # Loaders - Unified Factory
    # -----------------------------------------------------------------------
    @classmethod
    def load(cls, path: Union[str, Path]) -> "Skill":
        """
        Unified entry point to load a skill from a path.
        Dispatches to the appropriate loader based on the path.
        """
        from .loaders import ClaudeSkillLoader, CursorSkillLoader, GitHubSkillLoader
        
        path = Path(path).resolve()
        
        # Define available loaders in priority order
        loaders = [
            ClaudeSkillLoader(), # Checks for SKILL.md in dir or file
            CursorSkillLoader(), # Checks for .mdc
            GitHubSkillLoader(), # Checks for .md (generic)
        ]
        
        for loader in loaders:
            if loader.can_load(path):
                try:
                    return loader.load(path)
                except Exception as e:
                    logger.warning(f"Loader {loader.__class__.__name__} failed for {path}: {e}")
                    # Continue trying other loaders? Or fail? 
                    # Usually if can_load is true, it claims it. So we should probably fail.
                    raise e
                    
        raise InvalidSkillError(f"No suitable loader found for skill at {path}")

    # -----------------------------------------------------------------------
    # Serialisation helpers
    # -----------------------------------------------------------------------
    def to_tool_definition(self) -> Dict[str, Any]:
        """Return an OpenAI / Claude compatible tool definition."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }

    def to_anthropic_files(self) -> List[tuple]:
        """
        Walk the entire skill directory and return
        (relative_path, file_content, mime_type) tuples
        for uploading via `client.beta.skills.create(files=...)`.
        """
        files: List[tuple] = []
        try:
            # If path is a file (single file skill), just return that file?
            if self.path.is_file():
                 mime, _ = mimetypes.guess_type(str(self.path))
                 mime = mime or "application/octet-stream"
                 content = self.path.read_text(encoding="utf-8") # or bytes? safe_read_file is text
                 files.append((self.path.name, content, mime))
                 return files

            # Directory walking
            for item in sorted(self.path.rglob("*")):
                if any(part in _SKIP_PATTERNS for part in item.parts):
                    continue
                if item.is_dir():
                    continue

                rel = str(item.relative_to(self.path))
                mime, _ = mimetypes.guess_type(str(item))
                mime = mime or "application/octet-stream"

                content = safe_read_file(rel, self.path)
                files.append((rel, content, mime))

        except Exception as e:
            raise SecurityError(f"Failed to read skill files for upload: {e}")

        return files


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
class SkillRegistry:
    """Manages a collection of skills."""

    def __init__(self):
        self.skills: Dict[str, Skill] = {}

    def register_directory(self, root_dir: str) -> None:
        """Recursively search for SKILL.md files and register them."""
        # Use auto_discover for smarter loading? 
        # Or keep this strictly for valid "Anthropic Style" skills?
        # For backward compatibility, let's keep strict behavior but use new Loaders?
        # Actually, let's make it smarter.
        self.auto_discover(root_dir)

    def auto_discover(self, root_dir: str) -> None:
        """
        Recursively scans the directory for any supported skill formats.
        """
        root = Path(root_dir).resolve()
        if not root.exists():
             # It's okay if not exists, just warn? Or raise?
             # existing behavior raised FileNotFoundError
             raise FileNotFoundError(f"Directory not found: {root}")

        # Strategy: Walk directory and try to load EVERYTHING that looks like a skill
        # 1. Look for .claude/skills
        # 2. Look for .cursor/rules
        # 3. Look for .github/skills
        # 4. Recursively scan for SKILL.md
        
        # Current naive approach: Walk everything?
        # Better: Check standard paths first.
        
        known_paths = [
            root / ".claude" / "skills",
            root / ".cursor" / "rules",
            root / ".github" / "skills",
            root # scan root itself for SKILL.md or skills/ dir?
        ]
        
        # We also want to support `skills/` dir at root which was previous convention?
        # The previous code recursively searched `rglob("SKILL.md")`.
        
        # Let's do a recursive scan of the whole root, but optimized?
        # or just target specific agent directories if they exist, plus generic recursive search.
        
        # For simplicity and robustness:
        # 1. Recursive scan for SKILL.md (Claude standard)
        for skill_file in root.rglob("SKILL.md"):
             self._try_load(skill_file.parent)

        # 2. Recursive scan for .mdc (Cursor)
        for mdc_file in root.rglob("*.mdc"):
             self._try_load(mdc_file)

        # 3. Scan .github/skills/*.md (Copilot) specifically
        # We don't want to load every .md file in the repo!
        github_skills = root / ".github" / "skills"
        if github_skills.exists():
            for md_file in github_skills.glob("*.md"):
                if md_file.name != "README.md": # simple exclude
                    self._try_load(md_file)
    
    def _try_load(self, path: Path):
        try:
             skill = Skill.load(path)
             if skill.name in self.skills:
                 logger.warning(
                     "Overwriting duplicate skill '%s' from %s",
                     skill.name,
                     path,
                 )
             self.skills[skill.name] = skill
             logger.info(f"Loaded skill '{skill.name}' from {path}")
        except (InvalidSkillError, SecurityError) as e:
             logger.warning("Skipping invalid skill in %s: %s", path, e)
        except Exception as e:
             logger.error("Error loading skill from %s: %s", path, e)

    def get_skill(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)

    def list_skills(self) -> List[Skill]:
        return list(self.skills.values())

