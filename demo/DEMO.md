# Py LLM Skills - Core Demo

This demo illustrates:
1.  **Skill Registry**: Loading skills from a directory.
2.  **Skill Introspection**: Inspecting metadata and resources.
3.  **Pattern Generation**: Creating prompts from skills.
4.  **Automated Selection**: Using an LLM Router to pick relevant skills.
5.  **LLM Integration**: Using the selected skills to answer a query.

## Installation

This project uses `pyproject.toml` with optional dependencies aka "extras".

### 1. Recommended (Install Everything)
This installs the core library along with OpenAI SDK, Anthropic SDK, and python-dotenv.

```bash
uv pip install -e ".[full]"
# Or with standard pip
pip install -e ".[full]"
```

### 2. Lite (Core Only)
Installs only the lightweight core. Useful if you want to bring your own LLM client or minimize dependencies.

```bash
uv pip install -e .
```

To add specific integrations later:
```bash
uv pip install -e ".[openai]"
uv pip install -e ".[anthropic]"
```

## Setup

Create a `.env` file in the project root (or export env vars):

```bash
OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-... (If using Claude)
```

## Running the Demo

```bash
python demo/core_demo.py
```

## Expected Output

You should see:
1.  Skills loading from `demo/skills`.
2.  Inspection of "weather" and "pdf-processing" skills.
3.  **Automated Selection**: The router should pick `['weather']` for the query "What is the weather in Tokyo?".
4.  **Final Answer**: The LLM should generate a response using the injected skill context.
