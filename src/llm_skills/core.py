import re
import logging
import mimetypes
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ValidationError, field_validator
import yaml

from .utils import safe_read_file
from .exceptions import InvalidSkillError, SecurityError

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
    Represents an AI Agent Skill loaded from a directory (SKILL.md).
    Follows the Anthropic progressive disclosure pattern:
      Phase 1 – Metadata Discovery  (name + description)
      Phase 2 – File Loading         (all files → /skills/{dir}/)
      Phase 3 – Automatic Use        (Claude reads SKILL.md when relevant)
      Phase 4 – Composition          (multiple skills work together)
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
    # Loaders
    # -----------------------------------------------------------------------
    @classmethod
    def load(cls, skill_dir: Path) -> "Skill":
        """Load a skill from a directory containing SKILL.md."""
        skill_dir = Path(skill_dir).resolve()
        skill_file = skill_dir / "SKILL.md"

        if not skill_file.exists():
            raise FileNotFoundError(f"SKILL.md not found in {skill_dir}")

        content = safe_read_file("SKILL.md", skill_dir)

        # --- Parse frontmatter -----------------------------------------------
        try:
            parts = content.split("---", 2)
            if len(parts) < 3:
                raise InvalidSkillError(
                    f"SKILL.md in {skill_dir} is missing YAML frontmatter."
                )

            frontmatter_str = parts[1]
            instructions = parts[2].strip()

            metadata = yaml.safe_load(frontmatter_str)
            if not isinstance(metadata, dict):
                raise InvalidSkillError(f"Invalid YAML metadata in {skill_file}")

            # Pop known fields; everything else goes to extra_metadata
            input_schema = metadata.pop("input_schema", None) or QueryInput.model_json_schema()

            known_keys = {"name", "description", "version", "author", "license"}
            known = {k: metadata.pop(k) for k in list(metadata) if k in known_keys}
            extra_metadata = metadata  # whatever remains

            # --- Discover companion resources --------------------------------
            resources = cls._discover_resources(skill_dir)

            return cls(
                name=known.get("name"),
                description=known.get("description"),
                version=known.get("version", "0.1.0"),
                author=known.get("author"),
                license=known.get("license"),
                instructions=instructions,
                input_schema=input_schema,
                resources=resources,
                extra_metadata=extra_metadata,
                path=skill_dir,
            )

        except yaml.YAMLError as e:
            raise InvalidSkillError(f"YAML parsing error in {skill_file}: {e}")
        except ValidationError as e:
            raise InvalidSkillError(f"Validation error for skill in {skill_dir}: {e}")

    @staticmethod
    def _discover_resources(skill_dir: Path) -> Dict[str, List[str]]:
        """
        Walk the skill directory and categorise companion files.

        Categories:
          scripts   – .py, .sh, .bash files
          examples  – files whose name contains 'example'
          references – other .md files (excluding SKILL.md)
          data      – everything else (templates, configs, etc.)
        """
        resources: Dict[str, List[str]] = {}

        for item in sorted(skill_dir.rglob("*")):
            # Skip hidden / junk directories
            if any(part in _SKIP_PATTERNS for part in item.parts):
                continue
            if item.is_dir():
                continue
            rel = item.relative_to(skill_dir)
            rel_str = str(rel)

            # Skip the main SKILL.md
            if rel_str == "SKILL.md":
                continue

            # Categorise
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
        root = Path(root_dir).resolve()
        if not root.exists():
            raise FileNotFoundError(f"Directory not found: {root}")

        for skill_file in root.rglob("SKILL.md"):
            skill_dir = skill_file.parent
            try:
                skill = Skill.load(skill_dir)
                if skill.name in self.skills:
                    logger.warning(
                        "Overwriting duplicate skill '%s' from %s",
                        skill.name,
                        skill_dir,
                    )
                self.skills[skill.name] = skill
            except (InvalidSkillError, SecurityError) as e:
                logger.warning("Skipping invalid skill in %s: %s", skill_dir, e)
            except Exception as e:
                logger.error("Error loading skill from %s: %s", skill_dir, e)

    def get_skill(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)

    def list_skills(self) -> List[Skill]:
        return list(self.skills.values())
