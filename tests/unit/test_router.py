import pytest
from unittest.mock import MagicMock
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from py_llm_skills import SkillRouter, SkillRegistry, Skill

@pytest.fixture
def registry():
    reg = SkillRegistry()
    skill = Skill(
        name="weather",
        description="Get weather.",
        version="1.0.0",
        instructions="Fetch weather.",
        input_schema={},
        path="/tmp"
    )
    reg.skills["weather"] = skill
    return reg

def test_router_select_skill(registry):
    # Mock LLM Client
    mock_client = MagicMock()
    # Simulate Structured Output Response
    mock_response = MagicMock()
    mock_response.selected_skills = ["weather"]
    mock_client.chat_completion_with_structure.return_value = mock_response

    router = SkillRouter(llm_client=mock_client)
    selected = router.select_skill("Check rain", registry)
    
    assert len(selected) == 1
    assert selected[0].name == "weather"
    mock_client.chat_completion_with_structure.assert_called_once()

def test_router_no_skill(registry):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.selected_skills = []
    mock_client.chat_completion_with_structure.return_value = mock_response

    router = SkillRouter(llm_client=mock_client)
    selected = router.select_skill("Make a sandwich", registry)
    
    assert len(selected) == 0
