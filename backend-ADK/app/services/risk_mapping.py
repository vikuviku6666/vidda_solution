import json
from google.adk.tools import FunctionTool

RISK_TYPES = [
    'onboarding_risk',
    'sanctions_risk',
    'audit_trail_risk',
    'escalation_risk',
    'beneficial_ownership_risk',
]


RISK_KEYWORDS = {
    'onboarding_risk': [
        'onboard',
        'new customer',
        'new client',
        'kyc',
        'customer due diligence',
        'cdd',
        'enhanced due diligence',
        'edd',
        'identity verification',
    ],
    'sanctions_risk': [
        'sanction',
        'ofac',
        'screening',
        'watchlist',
        'restricted party',
        'pep',
        'politically exposed',
    ],
    'audit_trail_risk': [
        'audit',
        'record',
        'documentation',
        'document',
        'evidence',
        'log',
        'retain',
        'trace',
        'case notes',
    ],
    'escalation_risk': [
        'escalate',
        'escalation',
        'suspicious activity',
        'sar',
        'flag',
        'alert',
        'investigate',
        'exception',
        'manager review',
    ],
    'beneficial_ownership_risk': [
        'beneficial owner',
        'beneficial ownership',
        'ubo',
        'ownership',
        'control person',
        'corporate structure',
        'entity structure',
        'legal entity',
    ],
}


def map_responsibilities_to_risks(
    responsibilities: list[str],
) -> list[dict[str, list[str] | str]]:
    return [
        {
            'responsibility': responsibility,
            'risks': _match_risks(responsibility),
        }
        for responsibility in responsibilities
    ]


def _match_risks(responsibility: str) -> list[str]:
    normalized = responsibility.lower()

    matched_risks = [
        risk_type
        for risk_type, keywords in RISK_KEYWORDS.items()
        if any(keyword in normalized for keyword in keywords)
    ]

    return matched_risks

def search_risk_mapping_rag(role_query: str) -> dict:
    """
    Search the company's Risk Mapping RAG system.
    This system maps roles to compliance risks. Use this tool FIRST
    to understand what risks are associated with a role.
    
    Args:
        role_query: Description of the role and responsibilities.
    """
    risks = set()
    mappings = map_responsibilities_to_risks([role_query])
    for mapping in mappings:
        risks.update(mapping['risks'])
    
    return {"risks": list(risks)}

risk_mapping_tool = FunctionTool(func=search_risk_mapping_rag)
