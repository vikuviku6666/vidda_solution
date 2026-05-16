from fastapi import APIRouter

from app.models.risk_mapping import RiskMappingRequest, RiskMappingResponse
from app.services.risk_mapping import RISK_TYPES, map_responsibilities_to_risks


router = APIRouter()


@router.post('/map-risks', response_model=RiskMappingResponse)
def map_risks(request: RiskMappingRequest) -> RiskMappingResponse:
    return RiskMappingResponse(
        risk_types=RISK_TYPES,
        mappings=map_responsibilities_to_risks(request.responsibilities),
    )
