from pydantic import BaseModel, ConfigDict, Field

from app.models.competency import Competency
from app.models.regulation import RegulationReference


class Recommendation(BaseModel):
    model_config = ConfigDict(extra='forbid')

    quarter: str
    module: str
    objective: str
    behavioural_outcome: str
    activities: list[str] = Field(description="5-6 distinct training activities for this quarter")
    explanation: str
    role_reference: str
    risk_reference: str
    regulation_reference: str
    competency_reference: str


class TrainingPlan(BaseModel):
    model_config = ConfigDict(extra='forbid')

    role: str
    quarterly_plan: list[Recommendation]


class TrainingRecommendationRequest(BaseModel):
    role: str
    responsibilities: list[str] = Field(default_factory=list)
    risk_types: list[str] = Field(default_factory=list)
    competencies: Competency
    regulations: list[RegulationReference] = Field(default_factory=list)
