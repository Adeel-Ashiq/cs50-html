from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=1000, description="Legal question or case description in Urdu or English")
    top_k: Optional[int] = Field(default=6, ge=1, le=15)


class ConstitutionResult(BaseModel):
    id: str
    title: str
    text: str
    source: str
    score: Optional[float] = None


class ActResult(BaseModel):
    id: str
    act_name: str
    section: str
    title: str
    text: str
    source: str
    score: Optional[float] = None


class JudgmentResult(BaseModel):
    id: str
    case_name: str
    citation: str
    court: str
    year: int
    judges: List[str]
    summary: str
    key_holdings: List[str]
    relevant_acts: List[str]
    source: str
    score: Optional[float] = None


class LegalArgument(BaseModel):
    title: str
    description: str
    supporting_references: List[str]


class QueryResponse(BaseModel):
    query: str
    constitution_articles: List[ConstitutionResult]
    relevant_acts: List[ActResult]
    similar_judgments: List[JudgmentResult]
    suggested_arguments: List[LegalArgument]
    disclaimer: str = "This is an AI-assisted research tool for educational/demo purposes only. Always verify with original sources and consult a qualified lawyer. Not a substitute for professional legal advice."


class HealthResponse(BaseModel):
    status: str
    version: str
    documents_loaded: int
