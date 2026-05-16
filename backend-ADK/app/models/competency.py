from pydantic import BaseModel, ConfigDict, Field

from app.models.regulation import RegulationReference


class Competency(BaseModel):
    model_config = ConfigDict(extra='forbid')

    knowledge: list[str]
    skills: list[str]
    judgement: list[str]


class CompetencyRequest(BaseModel):
    role: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    risk_types: list[str] = Field(default_factory=list)
    regulations: list[RegulationReference] = Field(default_factory=list)
