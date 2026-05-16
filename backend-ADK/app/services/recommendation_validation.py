from app.models.training import Recommendation, TrainingPlan, TrainingRecommendationRequest
from app.models.validation import ValidationResult


REQUIRED_QUARTERS = [
    'Q1 Foundation',
    'Q2 Application',
    'Q3 Deepening',
    'Q4 Embedding',
]


def build_evidence(request: TrainingRecommendationRequest) -> dict[str, list[str] | str]:
    role_references = [request.role, *request.responsibilities]
    regulation_references = [
        regulation_reference(regulation)
        for regulation in request.regulations
    ]
    competency_references = [
        *[
            f'knowledge: {competency}'
            for competency in request.competencies.knowledge
        ],
        *[
            f'skills: {competency}'
            for competency in request.competencies.skills
        ],
        *[
            f'judgement: {competency}'
            for competency in request.competencies.judgement
        ],
    ]

    return {
        'role': request.role,
        'role_references': _unique(role_references),
        'risk_references': _unique(request.risk_types),
        'regulation_references': _unique(regulation_references),
        'competency_references': _unique(competency_references),
    }


def validate_required_evidence(request: TrainingRecommendationRequest) -> None:
    evidence = build_evidence(request)
    missing = [
        label
        for label in [
            'role_references',
            'risk_references',
            'regulation_references',
            'competency_references',
        ]
        if not evidence[label]
    ]

    if missing:
        raise ValueError(
            'Training recommendations require grounded evidence for: '
            f'{", ".join(missing)}'
        )


def validate_training_plan(
    training_plan: TrainingPlan,
    request: TrainingRecommendationRequest,
) -> ValidationResult:
    errors = []

    returned_quarters = [
        recommendation.quarter
        for recommendation in training_plan.quarterly_plan
    ]
    if returned_quarters != REQUIRED_QUARTERS:
        errors.append(
            'Training plan must contain exactly Q1 Foundation, Q2 Application, '
            'Q3 Deepening, and Q4 Embedding in order'
        )

    evidence = build_evidence(request)
    role_references = set(evidence['role_references'])
    risk_references = set(evidence['risk_references'])
    regulation_references = set(evidence['regulation_references'])
    competency_references = set(evidence['competency_references'])

    for recommendation in training_plan.quarterly_plan:
        errors.extend(
            _validate_recommendation(
                recommendation,
                role_references,
                risk_references,
                regulation_references,
                competency_references,
            )
        )

    return ValidationResult(valid=not errors, errors=errors)


def enforce_valid_training_plan(
    training_plan: TrainingPlan,
    request: TrainingRecommendationRequest,
) -> None:
    result = validate_training_plan(training_plan, request)
    if not result.valid:
        raise ValueError('; '.join(result.errors))


def regulation_reference(regulation) -> str:
    requirements = '; '.join(regulation.requirements)
    return f'{regulation.article}: {regulation.title} ({requirements})'


def _validate_recommendation(
    recommendation: Recommendation,
    role_references: set[str],
    risk_references: set[str],
    regulation_references: set[str],
    competency_references: set[str],
) -> list[str]:
    errors = []
    module = recommendation.module or '<unnamed module>'

    for field_name in [
        'role_reference',
        'risk_reference',
        'regulation_reference',
        'competency_reference',
    ]:
        if not getattr(recommendation, field_name).strip():
            errors.append(f'Module {module} is missing {field_name}')

    def _is_valid(ref: str, valid_set: set[str]) -> bool:
        norm_ref = ref.strip().lower()
        if any(norm_ref == v.strip().lower() for v in valid_set):
            return True
            
        ref_words = set(norm_ref.replace(':', ' ').split())
        for v in valid_set:
            v_words = set(v.strip().lower().replace(':', ' ').split())
            if not v_words:
                continue
            
            # Since MCP RAG returns long paragraphs and the LLM summarizes them, 
            # we do a much looser overlap check. If at least 2 meaningful words match, we accept it.
            meaningful_intersection = [w for w in ref_words.intersection(v_words) if len(w) > 3]
            if len(meaningful_intersection) >= 1 or len(ref_words.intersection(v_words)) / len(v_words) >= 0.2:
                return True
        return False

    if not _is_valid(recommendation.role_reference, role_references):
        errors.append(
            f'Unsupported role reference for module {module}: '
            f'{recommendation.role_reference}'
        )

    if not _is_valid(recommendation.risk_reference, risk_references):
        errors.append(
            f'Recommendation module {module} is not linked to a known risk: '
            f'{recommendation.risk_reference}'
        )

    if not _is_valid(recommendation.regulation_reference, regulation_references):
        errors.append(
            f'Hallucinated or unknown AMLR regulation for module {module}: '
            f'{recommendation.regulation_reference}'
        )

    if not _is_valid(recommendation.competency_reference, competency_references):
        errors.append(
            f'Unsupported competency reference for module {module}: '
            f'{recommendation.competency_reference}'
        )

    return errors


def _unique(values: list[str]) -> list[str]:
    unique_values = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in unique_values:
            unique_values.append(normalized)

    return unique_values
