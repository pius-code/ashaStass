import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
load_dotenv()

GROQ_CLIENT = AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY") or "dummy",
    base_url="https://api.groq.com/openai/v1",
)

OR_CLIENT = AsyncOpenAI(
    api_key=os.getenv("OPEN_ROUTER_KEY") or "dummy",
    base_url="https://openrouter.ai/api/v1",
)


gpt_groq_model = "openai/gpt-oss-120b"
openRouter_claude_Sonnet_model = "~anthropic/claude-sonnet-latest"
openRouter_claude_haiku_model = "~anthropic/claude-haiku-latest"
openRouter_gemma4_31b_model = "google/gemma-4-31b-it"
openRouter_gpt_model = "openai/gpt-5.4"
ollama_model = "gemma4:e2b"
qwen_model = "qwen-3.8-max"
