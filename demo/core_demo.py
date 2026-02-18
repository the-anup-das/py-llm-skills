import sys
import os
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add src directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from py_llm_skills import SkillRegistry, Skill, SkillRouter, Patterns
from py_llm_skills.llm.openai import OpenAIRequestClient, OpenAISDKAdapter

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

    # --- 5. Automated Skill Selection & LLM Call ---------------------------
    print("\n" + "=" * 60)
    print("  Automated Skill Selection & LLM Call")
    print("=" * 60)

    # 1. Setup LLM Client
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    llm_client = None
    client_type = "none"

    if openai_key:
        print(f"🔑 Found OPENAI_API_KEY")
        # Check if OpenAI SDK is installed to use Adapter, else use RequestClient
        try:
            import openai
            print("   Using OpenAI SDK Adapter")
            llm_client = OpenAISDKAdapter(openai.OpenAI(api_key=openai_key))
            client_type = "openai_sdk"
        except ImportError:
            print("   Using Lightweight OpenAI Request Client")
            llm_client = OpenAIRequestClient(api_key=openai_key)
            client_type = "openai_request"
            
    elif anthropic_key:
        print(f"🔑 Found ANTHROPIC_API_KEY (Router not yet supported for Anthropic, skipping)")
        # For this demo, router uses OpenAI format. 
        # Future: Abstract router to support Anthropic.
    else:
        print("⚠️  No API Key found (OPENAI_API_KEY). Skipping LLM demo.")

    if llm_client:
        # 2. Router
        router = SkillRouter(llm_client=llm_client)
        
        user_query = "What is the weather in Tokyo?"
        print(f"\n❓ User Query: \"{user_query}\"")
        
        print("🤔 Selecting skills...")
        selected_skills = router.select_skill(user_query, registry)
        
        if selected_skills:
            print(f"✅ Selected Skill(s): {[s.name for s in selected_skills]}")
            
            # 3. Final Answer
            print("\n🤖 Generating Final Answer...")
            
            # Construct System Prompt with selected skills (Pattern 1)
            system_prompt = Patterns.file_based_prompt(selected_skills)
            
            # Add directive to use the skill info (Simulating RAG/Context injection)
            # In a real agent loop, we'd execute the tool. Here we just show the context injection.
            system_prompt += "\nUse the above skill information to answer the user's question if possible, or describe how you would use it."

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ]
            
            response = llm_client.chat_completion(messages)
            
            # Extract content
            final_content = ""
            if client_type == "openai_request":
                final_content = response['choices'][0]['message']['content']
            elif client_type == "openai_sdk":
                final_content = response.choices[0].message.content
                
            print(f"\n📝 LLM Response:\n{final_content}")
            
        else:
            print("❌ No relevant skills found.")

if __name__ == "__main__":
    main()
