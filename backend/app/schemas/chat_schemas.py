from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    course_id: Optional[str] = None # Optional context
    chapter_id: Optional[str] = None # Optional context
    message: str # The user's question

class ChatResponse(BaseModel):
    answer: str
    suggested_followup: Optional[str] = None
