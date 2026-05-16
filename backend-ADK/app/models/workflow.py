from pydantic import BaseModel, ConfigDict, Field

from app.models.competency import Competency
from app.models.regulation import RegulationReference
from app.models.role_intelligence import RoleExtraction
from app.models.training import Recommendation


class WorkflowRequest(BaseModel):
    uploaded_text: str = Field(..., min_length=1)


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')

    uploaded_text: str
    role_data: RoleExtraction
    risks: list[str]
    regulations: list[RegulationReference]
    competencies: Competency
    recommendations: list[Recommendation]
    training_plan_id: str | None = None
