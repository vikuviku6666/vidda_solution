import json
from functools import lru_cache
from pathlib import Path

from google.adk.tools import FunctionTool
from app.models.regulation import RegulationReference


DATA_PATH = Path(__file__).resolve().parents[1] / 'data' / 'amlr_references.json'


@lru_cache(maxsize=1)
def load_regulation_references() -> list[RegulationReference]:
    data = json.loads(DATA_PATH.read_text(encoding='utf-8'))
    return [RegulationReference.model_validate(item) for item in data]


def retrieve_regulations(
    query: str | None = None,
    risk_types: list[str] | None = None,
) -> list[RegulationReference]:
    references = load_regulation_references()
    normalized_query = (query or '').lower().strip()
    requested_risks = set(risk_types or [])

    if not normalized_query and not requested_risks:
        return references

    return [
        reference
        for reference in references
        if _matches_query(reference, normalized_query)
        or _matches_risk_types(reference, requested_risks)
    ]


def _matches_query(reference: RegulationReference, query: str) -> bool:
    if not query:
        return False

    searchable_values = [
        reference.article,
        reference.title,
        *reference.requirements,
        *reference.keywords,
    ]

    return any(query in value.lower() for value in searchable_values)


def _matches_risk_types(
    reference: RegulationReference,
    requested_risks: set[str],
) -> bool:
    if not requested_risks:
        return False

    return bool(requested_risks.intersection(reference.risk_types))


def search_knowledge_index(query: str, risk_types: list[str] = None) -> list[dict]:
    """
    Search the AMLR regulation database.
    Use this to find specific regulatory requirements based on risks or keywords.
    
    Args:
        query: Natural language query or keywords.
        risk_types: Optional list of risk types to filter by.
    """
    results = retrieve_regulations(query, risk_types)
    return [r.model_dump() for r in results]

regulation_tool = FunctionTool(func=search_knowledge_index)
