import pytest
from pathlib import Path
from py_llm_skills.loaders import ClaudeSkillLoader, CursorSkillLoader, GitHubSkillLoader
from py_llm_skills.core import Skill

@pytest.fixture
def temp_skills_dir(tmp_path):
    return tmp_path

def test_claude_loader(temp_skills_dir):
    # Setup
    skill_dir = temp_skills_dir / "test-claude-skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("""---
name: claude-skill
description: A test claude skill
---
Do this.
""")
    
    loader = ClaudeSkillLoader()
    assert loader.can_load(skill_dir)
    assert loader.can_load(skill_file)
    
    skill = loader.load(skill_dir)
    assert skill.name == "claude-skill"
    assert skill.instructions == "Do this."

def test_cursor_loader(temp_skills_dir):
    # Setup
    rule_file = temp_skills_dir / "my-rule.mdc"
    rule_file.write_text("""---
description: A cursor rule
globs: *.py
---
Always utilize typing.
""")
    
    loader = CursorSkillLoader()
    assert loader.can_load(rule_file)
    
    skill = loader.load(rule_file)
    assert skill.name == "my-rule" # inferred from filename
    assert skill.description == "A cursor rule"
    assert skill.instructions == "Always utilize typing."
    assert skill.extra_metadata["globs"] == "*.py"

def test_github_loader(temp_skills_dir):
    # Setup
    skill_file = temp_skills_dir / "github-skill.md"
    skill_file.write_text("""---
name: copilot-helper
description: Helper for copilot
---
Be helpful.
""")
    
    loader = GitHubSkillLoader()
    assert loader.can_load(skill_file)
    
    skill = loader.load(skill_file)
    assert skill.name == "copilot-helper"
    assert skill.description == "Helper for copilot"
    assert skill.instructions == "Be helpful."
