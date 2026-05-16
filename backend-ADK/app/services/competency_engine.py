from app.models.competency import Competency
from app.models.regulation import RegulationReference


RISK_COMPETENCY_MAP = {
    'onboarding_risk': Competency(
        knowledge=[
            'Customer due diligence requirements',
            'Enhanced due diligence triggers',
        ],
        skills=[
            'Verify customer identity and onboarding evidence',
            'Apply risk-based onboarding checks',
        ],
        judgement=[
            'Identify when onboarding information is incomplete or inconsistent',
        ],
    ),
    'sanctions_risk': Competency(
        knowledge=[
            'Sanctions screening obligations',
            'Watchlist and politically exposed person risk concepts',
        ],
        skills=[
            'Review potential sanctions screening matches',
            'Document screening decisions and false positive rationale',
        ],
        judgement=[
            'Escalate credible sanctions exposure before customer acceptance or activity continues',
        ],
    ),
    'audit_trail_risk': Competency(
        knowledge=[
            'Recordkeeping and evidence retention expectations',
            'Audit trail requirements for compliance decisions',
        ],
        skills=[
            'Create clear case notes and decision records',
            'Link evidence to the relevant control or requirement',
        ],
        judgement=[
            'Assess whether documentation is sufficient for audit or regulator review',
        ],
    ),
    'escalation_risk': Competency(
        knowledge=[
            'Escalation paths for suspicious activity and control exceptions',
            'Suspicious activity indicators and reporting triggers',
        ],
        skills=[
            'Triage alerts and exceptions',
            'Escalate suspicious activity with concise supporting evidence',
        ],
        judgement=[
            'Distinguish routine anomalies from issues requiring formal escalation',
        ],
    ),
    'beneficial_ownership_risk': Competency(
        knowledge=[
            'Beneficial ownership identification requirements',
            'Ownership and control structure risk indicators',
        ],
        skills=[
            'Analyze legal entity ownership structures',
            'Identify ultimate beneficial owners and control persons',
        ],
        judgement=[
            'Recognize complex ownership structures that require enhanced review',
        ],
    ),
}


def generate_competencies(
    role: str | None = None,
    responsibilities: list[str] | None = None,
    risk_types: list[str] | None = None,
    regulations: list[RegulationReference] | None = None,
) -> Competency:
    competencies = Competency(knowledge=[], skills=[], judgement=[])

    for risk_type in risk_types or []:
        risk_competency = RISK_COMPETENCY_MAP.get(risk_type)
        if risk_competency:
            _extend_unique(competencies.knowledge, risk_competency.knowledge)
            _extend_unique(competencies.skills, risk_competency.skills)
            _extend_unique(competencies.judgement, risk_competency.judgement)

    for regulation in regulations or []:
        _extend_unique(
            competencies.knowledge,
            [
                f'{regulation.article}: {regulation.title}',
                *regulation.requirements,
            ],
        )

    if role:
        _extend_unique(
            competencies.judgement,
            [f'Apply requirements in the context of the {role} role'],
        )

    for responsibility in responsibilities or []:
        _extend_unique(
            competencies.skills,
            [f'Perform responsibility: {responsibility}'],
        )

    return competencies


def _extend_unique(target: list[str], values: list[str]) -> None:
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in target:
            target.append(normalized)
