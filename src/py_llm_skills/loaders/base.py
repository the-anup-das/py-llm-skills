from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Dict, List, Any

if TYPE_CHECKING:
    from ..core import Skill

class BaseSkillLoader(ABC):
    """
    Abstract base class for Skill Loaders.
    Each loader handles a specific format (Claude, Cursor, GitHub, etc.)
    """

    @abstractmethod
    def can_load(self, path: Path) -> bool:
        """
        Return True if this loader can handle the given path.
        Use this to check file extensions, existence of specific files (e.g. SKILL.md), etc.
        """
        pass

    @abstractmethod
    def load(self, path: Path) -> "Skill":
        """
        Load the skill from the path.
        Must return a valid Skill object.
        """
        pass
