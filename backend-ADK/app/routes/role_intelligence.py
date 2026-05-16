from fastapi import APIRouter, HTTPException, status

from app.models.role_intelligence import RoleExtraction, RoleExtractionRequest
from app.services.role_intelligence import extract_role_intelligence


router = APIRouter()


@router.post('/extract-role', response_model=RoleExtraction)
def extract_role(request: RoleExtractionRequest) -> RoleExtraction:
    try:
        return extract_role_intelligence(request.text)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
