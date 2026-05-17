from openai import OpenAIError

from app.models.role_intelligence import RoleExtraction
from app.prompts.role_extraction import ROLE_EXTRACTION_SYSTEM_PROMPT
from app.services.audit import audit_log
from app.services.llm_client import create_llm_client, llm_model_name


def extract_role_intelligence(document_text: str) -> RoleExtraction:
    text = document_text.strip()
    if not text:
        raise ValueError('Document text is required')

    client = create_llm_client()
    model_name = llm_model_name()
    user_prompt = (
        'Extract role intelligence from this document text:\n\n'
        f'{_truncate_for_llm(text)}'
    )

    try:
        response = client.chat.completions.create(
            model=model_name,
            temperature=0,   # deterministic — same text → same extraction
            messages=[
                {
                    'role': 'system',
                    'content': ROLE_EXTRACTION_SYSTEM_PROMPT,
                },
                {
                    'role': 'user',
                    'content': user_prompt,
                },
            ],
            response_format={
                'type': 'json_schema',
                'json_schema': {
                    'name': 'role_extraction',
                    'schema': RoleExtraction.model_json_schema(),
                    'strict': True,
                },
            },
        )
    except OpenAIError as exc:
        raise RuntimeError(f'LLM extraction failed: {exc}') from exc

    content = response.choices[0].message.content
    if content is None:
        raise ValueError('LLM returned an empty response')

    role_extraction = RoleExtraction.model_validate_json(content)
    audit_log(
        'role_extraction',
        model_used=model_name,
        prompt={
            'system': ROLE_EXTRACTION_SYSTEM_PROMPT,
            'user': user_prompt,
        },
        output=role_extraction.model_dump(),
        references={
            'source': 'uploaded_text',
        },
        uploaded_docs={
            'text_length': len(text),
        },
    )

    return role_extraction

def _truncate_for_llm(text: str, max_chars: int = 24000) -> str:
    if len(text) <= max_chars:
        return text

    return text[:max_chars]
