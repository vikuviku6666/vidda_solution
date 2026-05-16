from fastapi import APIRouter, HTTPException, status

from app.models.training import TrainingPlan, TrainingRecommendationRequest
from app.services.training_recommendation import generate_training_recommendations


router = APIRouter()


@router.post('/training/recommendations', response_model=TrainingPlan)
def create_training_recommendations(
    request: TrainingRecommendationRequest,
) -> TrainingPlan:
    try:
        return generate_training_recommendations(request)
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
