import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


BACKEND_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BACKEND_DIR / '.env')
load_dotenv(BACKEND_DIR / '.env.local', override=True)


def create_llm_client() -> OpenAI:
    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError('Set OPENAI_API_KEY or OPENROUTER_API_KEY before LLM generation')

    base_url = os.getenv('LLM_BASE_URL') or os.getenv('OPENAI_BASE_URL')
    if not base_url and os.getenv('OPENROUTER_API_KEY'):
        base_url = 'https://openrouter.ai/api/v1'

    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)

    return OpenAI(api_key=api_key)


def llm_model_name() -> str:
    if os.getenv('LLM_MODEL'):
        return os.environ['LLM_MODEL']

    if os.getenv('OPENROUTER_API_KEY'):
        return 'openai/gpt-4o-mini'

    return 'gpt-4o-mini'
