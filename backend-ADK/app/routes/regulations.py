from fastapi import APIRouter

from app.models.regulation import RegulationSearchRequest, RegulationSearchResponse
from app.services.regulation_retrieval import retrieve_regulations


router = APIRouter()


@router.get('/regulations', response_model=RegulationSearchResponse)
def list_regulations() -> RegulationSearchResponse:
    return RegulationSearchResponse(matches=retrieve_regulations())


@router.post('/regulations/search', response_model=RegulationSearchResponse)
def search_regulations(request: RegulationSearchRequest) -> RegulationSearchResponse:
    return RegulationSearchResponse(
        matches=retrieve_regulations(
            query=request.query,
            risk_types=request.risk_types,
        )
    )
