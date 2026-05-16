from pydantic import BaseModel, ConfigDict, Field


class RiskMappingRequest(BaseModel):
    responsibilities: list[str] = Field(..., min_length=1)


class ResponsibilityRiskMapping(BaseModel):
    model_config = ConfigDict(extra='forbid')

    responsibility: str
    risks: list[str]


class RiskMappingResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')

    risk_types: list[str]
    mappings: list[ResponsibilityRiskMapping]
