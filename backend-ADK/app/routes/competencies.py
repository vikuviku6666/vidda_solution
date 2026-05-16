from fastapi import APIRouter

from app.models.competency import Competency, CompetencyRequest
from app.services.competency_engine import generate_competencies


router = APIRouter()


@router.post('/competencies', response_model=Competency)
def create_competencies(request: CompetencyRequest) -> Competency:
    return generate_competencies(
        role=request.role,
        responsibilities=request.responsibilities,
        risk_types=request.risk_types,
        regulations=request.regulations,
    )
