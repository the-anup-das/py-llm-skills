import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from py_llm_skills.core import Skill
from py_llm_skills.patterns import Patterns

@pytest.fixture
def mock_skill():
    return Skill(
        name="weather",
        description="Get weather.",
        version="1.0.0",
        instructions="Fetch weather data.",
        input_schema={"type": "object", "properties": {"loc": {"type": "string"}}},
        path="/tmp/weather"
    )

def test_file_based_prompt(mock_skill):
    prompt = Patterns.file_based_prompt([mock_skill])
    assert "### Skill: weather" in prompt
    assert "Description: Get weather." in prompt
    assert "Instructions:\nFetch weather data." in prompt

def test_tool_definitions(mock_skill):
    tools = Patterns.tool_definitions([mock_skill])
    assert len(tools) == 1
    assert tools[0]["type"] == "function"
    assert tools[0]["function"]["name"] == "weather"
