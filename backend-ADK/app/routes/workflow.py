from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.models.workflow import WorkflowRequest, WorkflowResponse
from app.services.workflow import run_training_workflow, revise_training_plan


router = APIRouter()

class ReviseRequest(BaseModel):
    feedback: str

@router.post('/workflow/run', response_model=WorkflowResponse)
def run_workflow(request: WorkflowRequest) -> WorkflowResponse:
    try:
        return run_training_workflow(request.uploaded_text)
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

@router.post('/workflow/revise/{plan_id}')
def revise_workflow(plan_id: str, request: ReviseRequest):
    try:
        success = revise_training_plan(plan_id, request.feedback)
        if not success:
            raise HTTPException(status_code=404, detail="Plan not found or revision failed")
        return {"status": "success", "message": "Plan revised successfully. Page will reload with updated plan."}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

@router.get('/workflow/plan/{plan_id}', response_model=WorkflowResponse)
def get_training_plan(plan_id: str):
    """Fetch a training plan by ID with all related data"""
    from app.services.workflow import get_plan_by_id
    try:
        plan_data = get_plan_by_id(plan_id)
        if not plan_data:
            raise HTTPException(status_code=404, detail="Plan not found")
        return plan_data
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

@router.get('/workflow/health')
def health_check():
    """Simple health check endpoint"""
    return {"status": "ok", "message": "Workflow service is running"}


@router.get('/workflow/plans')
def list_plans():
    """List all saved training plans (newest first)."""
    from app.db import SessionLocal
    from app.db_models import TrainingPlanRecord, RoleRecord, RecommendationRecord
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="Database not available")
    with SessionLocal() as db:
        plans = (
            db.query(TrainingPlanRecord)
            .order_by(TrainingPlanRecord.created_at.desc())
            .all()
        )
        result = []
        for p in plans:
            role = db.query(RoleRecord).filter(RoleRecord.id == p.role_id).first()
            module_count = db.query(RecommendationRecord).filter(
                RecommendationRecord.training_plan_id == p.id
            ).count()
            result.append({
                "plan_id":      p.id,
                "role":         role.name if role else "Unknown",
                "status":       p.status,
                "module_count": module_count,
                "created_at":   p.created_at.isoformat() if p.created_at else None,
            })
        return result
