import sys
import os
import json

# Add src directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from py_llm_skills import SkillRegistry, Patterns

def main():
    print("=" * 60)
    print("  02. Generate Prompts & Tool Definitions")
    print("=" * 60)

    registry = SkillRegistry()
    registry.register_directory(os.path.join(os.path.dirname(__file__), "skills"))
    weather = registry.get_skill("weather")

    if weather:
        # Pattern 1: File-based Prompt (System Prompt Injection)
        print("\n--- Pattern 1: System Prompt Injection ---")
        print(Patterns.file_based_prompt([weather]))

        # Pattern 2: Tool Definition (JSON Schema for Function Calling)
        print("\n--- Pattern 2: Tool Definition (JSON) ---")
        print(json.dumps(weather.to_tool_definition(), indent=2))

if __name__ == "__main__":
    main()
