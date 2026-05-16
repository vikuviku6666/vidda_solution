from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_session
from app.db_models import TrainingPlanRecord, RecommendationRecord, AuditLogRecord
from sqlalchemy import func

router = APIRouter()

class PlanUpdate(BaseModel):
    status: str | None = None
    reviewer_notes: str | None = None

class RecommendationUpdate(BaseModel):
    objective: str | None = None
    behavioural_outcome: str | None = None
    activities: list[str] | None = None

@router.patch('/training/plans/{plan_id}')
def update_training_plan(plan_id: str, payload: PlanUpdate, session: Session = Depends(get_session)):
    plan = session.query(TrainingPlanRecord).filter(TrainingPlanRecord.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    if payload.status:
        plan.status = payload.status
    if payload.reviewer_notes is not None:
        plan.reviewer_notes = payload.reviewer_notes
        
    session.commit()
    return {"status": "success"}

@router.put('/training/recommendations/{rec_id}')
def update_recommendation(rec_id: str, payload: RecommendationUpdate, session: Session = Depends(get_session)):
    rec = session.query(RecommendationRecord).filter(RecommendationRecord.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
        
    if payload.objective:
        rec.objective = payload.objective
    if payload.behavioural_outcome:
        rec.behavioural_outcome = payload.behavioural_outcome
    if payload.activities:
        rec.activities = payload.activities
        
    session.commit()
    return {"status": "success"}

@router.get('/governance/stats')
def get_governance_stats(session: Session = Depends(get_session)):
    approvals_pending = session.query(TrainingPlanRecord).filter(TrainingPlanRecord.status.in_(['draft', 'review', 'edit'])).count()
    published_count = session.query(TrainingPlanRecord).filter(TrainingPlanRecord.status == 'published').count()
    audit_events = session.query(AuditLogRecord).count()
    
    # Mock compliance score for now
    compliance_score = 0.91 + (published_count * 0.01)
    if compliance_score > 1.0:
        compliance_score = 1.0
        
    return {
        "approvalsPending": approvals_pending,
        "publishedCount": published_count,
        "auditEvents": audit_events,
        "complianceScore": compliance_score
    }
