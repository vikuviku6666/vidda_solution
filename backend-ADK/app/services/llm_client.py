import os
from pathlib import Path

import httpx
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

    # Separate connect (10s) vs read (90s) timeouts.
    # max_retries=1 avoids silent 2×90s waits when OpenRouter is slow.
    _timeout = httpx.Timeout(connect=10.0, read=90.0, write=10.0, pool=5.0)
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url, timeout=_timeout, max_retries=1)

    return OpenAI(api_key=api_key, timeout=_timeout, max_retries=1)


def llm_model_name() -> str:
    if os.getenv('LLM_MODEL'):
        return os.environ['LLM_MODEL']

    if os.getenv('OPENROUTER_API_KEY'):
        return 'openai/gpt-4o-mini'

    return 'gpt-4o-mini'
