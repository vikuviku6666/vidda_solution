from pydantic import BaseModel, ConfigDict, Field


class RegulationReference(BaseModel):
    model_config = ConfigDict(extra='forbid')

    article: str
    title: str
    requirements: list[str]
    keywords: list[str] = Field(default_factory=list)
    risk_types: list[str] = Field(default_factory=list)


class RegulationSearchRequest(BaseModel):
    query: str | None = None
    risk_types: list[str] = Field(default_factory=list)


class RegulationSearchResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')

    matches: list[RegulationReference]
