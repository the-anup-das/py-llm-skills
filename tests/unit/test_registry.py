import pytest
from unittest.mock import MagicMock, patch
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from py_llm_skills.core import SkillRegistry, Skill

@pytest.fixture
def mock_skill():
    return Skill(
        name="mock-skill",
        description="A mock skill.",
        version="1.0.0",
        instructions="Do something.",
        input_schema={"type": "object"},
        path="/tmp/mock"
    )

def test_registry_add_skill(mock_skill):
    registry = SkillRegistry()
    registry.skills["mock-skill"] = mock_skill
    
    assert len(registry.list_skills()) == 1
    assert registry.get_skill("mock-skill") == mock_skill

def test_registry_get_missing_skill():
    registry = SkillRegistry()
    assert registry.get_skill("missing") is None
