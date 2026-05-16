from pydantic import BaseModel, ConfigDict, Field


class RoleExtractionRequest(BaseModel):
    text: str = Field(..., min_length=1)


class RoleExtraction(BaseModel):
    model_config = ConfigDict(extra='forbid')

    role: str
    responsibilities: list[str]
    compliance_exposure: list[str]
    risk_indicators: list[str]
