from pydantic import BaseModel, Field


class ClassifyRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field("", max_length=2000)


class ClassifyResponse(BaseModel):
    category: str
    confidence: float
