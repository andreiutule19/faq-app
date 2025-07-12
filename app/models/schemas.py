from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class QuestionRequest(BaseModel):
    user_question: str = Field(..., min_length=1, max_length=1000)

class QuestionResponse(BaseModel):
    source: str
    matched_question: Optional[str] = None
    answer: str
    similarity_score: Optional[float] = None

class FAQEntryCreate(BaseModel):
    question: str
    answer: str
    collection: str = "default"

class FAQEntryResponse(BaseModel):
    id: int
    question: str
    answer: str
    collection: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class EmbeddingStats(BaseModel):
    total_entries: int
    collections: List[str]
    last_updated: Optional[datetime] = None