import json

from openai import OpenAIError

from app.models.training import TrainingPlan, TrainingRecommendationRequest
from app.prompts.training_generation import TRAINING_GENERATION_SYSTEM_PROMPT
from app.services.audit import audit_log
from app.services.llm_client import create_llm_client, llm_model_name
from app.services.recommendation_validation import (
    REQUIRED_QUARTERS,
    build_evidence,
    enforce_valid_training_plan,
    validate_required_evidence,
    validate_training_plan,
)


MAX_GENERATION_ATTEMPTS = 1


def generate_training_recommendations(
    request: TrainingRecommendationRequest,
) -> TrainingPlan:
    validate_required_evidence(request)
    client = create_llm_client()
    validation_errors: list[str] = []
    model_name = llm_model_name()

    for attempt in range(MAX_GENERATION_ATTEMPTS):
        training_plan = _generate_training_plan(
            client=client,
            request=request,
            validation_errors=validation_errors,
            model_name=model_name,
        )

        validation_result = validate_training_plan(training_plan, request)
        if validation_result.valid:
            audit_log(
                'training_recommendation',
                model_used=model_name,
                prompt={
                    'system': TRAINING_GENERATION_SYSTEM_PROMPT,
                    'payload': json.loads(
                        _generation_payload(request, validation_errors)
                    ),
                },
                output=training_plan.model_dump(),
                references=build_evidence(request),
                metadata={
                    'attempts': attempt + 1,
                    'validation_errors': validation_errors,
                },
            )
            return training_plan

        validation_errors = validation_result.errors
        if attempt == MAX_GENERATION_ATTEMPTS - 1:
            break

    raise ValueError(
        'Training generation failed validation after regeneration: '
        f'{"; ".join(validation_errors)}'
    )


def _generate_training_plan(
    client,
    request: TrainingRecommendationRequest,
    validation_errors: list[str],
    model_name: str,
) -> TrainingPlan:
    try:
        response = client.chat.completions.create(
            model=model_name,
            max_tokens=8000,
            messages=[
                {
                    'role': 'system',
                    'content': TRAINING_GENERATION_SYSTEM_PROMPT,
                },
                {
                    'role': 'user',
                    'content': _generation_payload(request, validation_errors),
                },
            ],
            response_format={
                'type': 'json_schema',
                'json_schema': {
                    'name': 'training_plan',
                    'schema': TrainingPlan.model_json_schema(),
                    'strict': True,
                },
            },
        )
    except OpenAIError as exc:
        raise RuntimeError(f'Training generation failed: {exc}') from exc

    content = response.choices[0].message.content
    if content is None:
        raise ValueError('LLM returned an empty training plan')

    return TrainingPlan.model_validate_json(content)


def _generation_payload(
    request: TrainingRecommendationRequest,
    validation_errors: list[str],
) -> str:
    payload = {
        'quarters': REQUIRED_QUARTERS,
        'evidence': build_evidence(request),
    }

    if validation_errors:
        payload['previous_validation_errors'] = validation_errors
        payload['instruction'] = (
            'Regenerate the complete training plan. Fix every validation error. '
            'Use only exact references from the evidence lists.'
        )

    return json.dumps(payload, indent=2)


def _validate_grounded_training_plan(
    training_plan: TrainingPlan,
    request: TrainingRecommendationRequest,
) -> None:
    enforce_valid_training_plan(training_plan, request)
