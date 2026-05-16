from pydantic import BaseModel, ConfigDict, Field


class ValidationResult(BaseModel):
    model_config = ConfigDict(extra='forbid')

    valid: bool
    errors: list[str] = Field(default_factory=list)
