import sys
import os
import json

# Add src directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from py_llm_skills import SkillRegistry

def main():
    print("=" * 60)
    print("  01. Explore Skills")
    print("=" * 60)

    # 1. Initialize Registry
    registry = SkillRegistry()
    skills_dir = os.path.join(os.path.dirname(__file__), "skills")
    print(f"\n📂 Loading skills from: {skills_dir}")
    registry.register_directory(skills_dir)

    # 2. List Skills
    skills = registry.list_skills()
    print(f"✅ Found {len(skills)} skill(s): {[s.name for s in skills]}")

    # 3. Inspect a specific skill (e.g., weather)
    weather = registry.get_skill("weather")
    if weather:
        print(f"\n--- Skill: {weather.name} (v{weather.version}) ---")
        print(f"Description: {weather.description}")
        print(f"Resources:   {weather.resources}")

    # 4. Inspect a complex skill (e.g., pdf-processing)
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

if __name__ == "__main__":
    main()
