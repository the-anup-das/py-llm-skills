import sys
import os
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from py_llm_skills import SkillRegistry, SkillRouter
from py_llm_skills.llm.openai import OpenAIRequestClient, OpenAISDKAdapter

def main():
    print("=" * 60)
    print("  03. Automated Skill Router")
    print("=" * 60)

    # 1. Setup
    registry = SkillRegistry()
    registry.register_directory(os.path.join(os.path.dirname(__file__), "skills"))

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("⚠️  OPENAI_API_KEY not found. Skipping.")
        return

    # Initialize Client (Adapter if SDK installed, else Request)
    try:
        import openai
        client = OpenAISDKAdapter(openai.OpenAI(api_key=openai_key))
    except ImportError:
        client = OpenAIRequestClient(api_key=openai_key)

    # 2. Initialize Router
    router = SkillRouter(llm_client=client)

    # 3. Test Queries
    queries = [
        "What is the weather in Tokyo?",
        "Extract text from this PDF invoice.",
        "How do I make a cake?" # Should return no skills
    ]

    for q in queries:
        print(f"\n❓ Query: \"{q}\"")
        selected = router.select_skill(q, registry)
        if selected:
            print(f"✅ Selected: {[s.name for s in selected]}")
        else:
            print("❌ No relevant skills found.")

if __name__ == "__main__":
    main()
