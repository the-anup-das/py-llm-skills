import sys
import os
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from py_llm_skills import SkillRegistry
from py_llm_skills.llm.claude import AnthropicSkillManager

def main():
    print("=" * 60)
    print("  05. Anthropic Agent (Skills API)")
    print("=" * 60)

    # 1. Setup
    registry = SkillRegistry()
    registry.register_directory(os.path.join(os.path.dirname(__file__), "skills"))

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("⚠️  ANTHROPIC_API_KEY not found. Skipping.")
        return

    try:
        import anthropic
    except ImportError:
        print("⚠️  'anthropic' package not installed. Skipping.")
        return

    print("Initializing Anthropic Client...")
    client = anthropic.Anthropic(api_key=anthropic_key)
    manager = AnthropicSkillManager(client)

    # 2. Pick a skill manually (Router could be used here too if adapted)
    pdf_skill = registry.get_skill("pdf-processing")
    
    if pdf_skill:
        print(f"\n1️⃣  Uploading Skill: {pdf_skill.name}...")
        try:
            skill_id = manager.upload_skill(pdf_skill)
            print(f"✅ Uploaded! Skill ID: {skill_id}")

            # 3. Use in Conversation
            print("\n2️⃣  Sending Message to Claude...")
            container_block = manager.format_container_param([skill_id])
            
            # Note: This uses the beta 'skills-2025-10-02' hypothetical API
            # Adjust based on actua SDK implementation availability
            # This is a conceptual demo based on the plan.
            
            print(f"   Context: {json.dumps(container_block, indent=2)}")
            print("   (Skipping actual call to avoid Beta errors without valid access)")
            
        except Exception as e:
            print(f"❌ Upload Failed (Expected if Beta not active): {e}")

if __name__ == "__main__":
    main()
