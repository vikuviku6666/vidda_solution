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
