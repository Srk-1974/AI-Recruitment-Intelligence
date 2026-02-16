from pydantic import BaseModel, Field
from typing import List

class EvaluationResult(BaseModel):
    match_percentage: int = Field(..., ge=0, le=100)
    matched_skills: List[str]
    missing_skills: List[str]
    experience_evaluation: str
    candidate_summary: str
    ranking: str # Strong Match, Moderate Match, Weak Match
    interview_questions: List[str] = []

class AnalysisRequest(BaseModel):
    resume_text: str
    jd_text: str
    model_name: str = "llama3.2"
    temperature: float = 0.1
    max_tokens: int = 2000
    api_key: str = None
    provider: str = "Ollama"

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []
    model_name: str = "llama3.2"
    temperature: float = 0.7
    max_tokens: int = 1000
    api_key: str = None
    provider: str = "Ollama"

class ChatResponse(BaseModel):
    response: str
