import sys
import os
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from py_llm_skills import SkillRegistry, SkillRouter, Patterns
from py_llm_skills.llm.openai import OpenAIRequestClient, OpenAISDKAdapter

def main():
    print("=" * 60)
    print("  04. OpenAI Agent (Process Flow)")
    print("=" * 60)

    # 1. Setup
    registry = SkillRegistry()
    registry.register_directory(os.path.join(os.path.dirname(__file__), "skills"))
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("⚠️  OPENAI_API_KEY not found. Skipping.")
        return

    try:
        import openai
        print("Using OpenAI SDK")
        raw_client = openai.OpenAI(api_key=openai_key)
        client = OpenAISDKAdapter(raw_client)
    except ImportError:
        print("Using Request Client")
        client = OpenAIRequestClient(api_key=openai_key)

    router = SkillRouter(llm_client=client)
    user_query = "What is the weather in Paris?"

    # 2. Route
    print(f"\n1️⃣  Routing Query: \"{user_query}\"")
    skills = router.select_skill(user_query, registry)
    print(f"   Selected: {[s.name for s in skills]}")

    if not skills:
        print("No skills found.")
        return

    # 3. Construct Context
    print("\n2️⃣  Constructing System Prompt (Pattern 1)")
    system_prompt = Patterns.file_based_prompt(skills)
    system_prompt += "\nUse the provided skill information to answer."

    # 4. Chat Completion
    print("\n3️⃣  Executing Chat Completion")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]
    
    # Note: In a real agent, we'd use tools=... and a loop.
    # Here we show the context injection pattern result.
    response = client.chat_completion(messages)
    
    content = ""
    if isinstance(response, dict):
        content = response['choices'][0]['message']['content']
    else:
        content = response.choices[0].message.content

    print(f"\n📝 Response:\n{content}")

if __name__ == "__main__":
    main()
