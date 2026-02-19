import sys
import os
import shutil
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from py_llm_skills import SkillRegistry, Skill

def setup_demo_environment(root: Path):
    if root.exists():
        shutil.rmtree(root)
    root.mkdir()

    # 1. Claude Skill
    claude_dir = root / ".claude" / "skills" / "weather-reporter"
    claude_dir.mkdir(parents=True)
    (claude_dir / "SKILL.md").write_text("""---
name: weather-reporter
description: Reports weather
---
Check the weather.
""")

    # 2. Cursor Rule
    cursor_dir = root / ".cursor" / "rules"
    cursor_dir.mkdir(parents=True)
    (cursor_dir / "code-style.mdc").write_text("""---
description: Enforce pep8
globs: *.py
---
Use PEP8.
""")

    # 3. GitHub Skill
    github_dir = root / ".github" / "skills"
    github_dir.mkdir(parents=True)
    (github_dir / "pr-reviewer.md").write_text("""---
name: pr-reviewer
description: Reviews PRs
---
Review the PR carefully.
""")

    print(f"✅ Created demo environment at: {root}")

def main():
    print("=" * 60)
    print("  04. Multi-Agent Skill Discovery")
    print("=" * 60)
    
    demo_root = Path("demo/multi_agent_repo")
    setup_demo_environment(demo_root)
    
    registry = SkillRegistry()
    print(f"\nScanning {demo_root}...")
    
    registry.register_directory(demo_root)
    
    skills = registry.list_skills()
    print(f"\nFound {len(skills)} skills:")
    
    for s in skills:
        print(f"- {s.name:<20} | {s.description}")

    # Cleanup
    # shutil.rmtree(demo_root)

if __name__ == "__main__":
    main()
