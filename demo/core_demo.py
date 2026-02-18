import sys
import os
import json

# Add src directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from py_llm_skills.core import SkillRegistry, Skill
from py_llm_skills.patterns import Patterns

def main():
    print("=" * 60)
    print("  Py LLM Skills – Core Demo")
    print("=" * 60)

    # --- 1. Registry -------------------------------------------------------
    registry = SkillRegistry()
    skills_dir = os.path.join(os.path.dirname(__file__), "skills")
    print(f"\n📂 Loading skills from: {skills_dir}")
    registry.register_directory(skills_dir)

    skills = registry.list_skills()
    print(f"✅ Found {len(skills)} skill(s): {[s.name for s in skills]}")

    # --- 2. Weather skill (simple) -----------------------------------------
    weather = registry.get_skill("weather")
    if weather:
        print(f"\n--- Skill: {weather.name} (v{weather.version}) ---")
        print(f"Description: {weather.description}")
        print(f"Resources:   {weather.resources}")
        print(f"\nTool Definition:")
        print(json.dumps(weather.to_tool_definition(), indent=2))

    # --- 3. PDF skill (multi-file) -----------------------------------------
    pdf = registry.get_skill("pdf-processing")
    if pdf:
        print(f"\n--- Skill: {pdf.name} (v{pdf.version}) ---")
        print(f"Description: {pdf.description}")
        print(f"Extra Meta:  {pdf.extra_metadata}")
        print(f"\n📁 Discovered Resources:")
        for category, files in pdf.resources.items():
            print(f"  {category}:")
            for f in files:
                print(f"    - {f}")

        print(f"\n📤 Files for Anthropic Upload ({len(pdf.to_anthropic_files())}):")
        for fname, _, mime in pdf.to_anthropic_files():
            print(f"  {fname}  ({mime})")

    # --- 4. Pattern: File-based Prompt -------------------------------------
    print("\n--- Pattern: File-based Prompt (weather only) ---")
    print(Patterns.file_based_prompt([weather]))

if __name__ == "__main__":
    main()
