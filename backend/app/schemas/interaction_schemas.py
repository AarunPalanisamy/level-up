from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# --- 1. Progress Tracking ---
class ChapterProgressUpdate(BaseModel):
    last_slide_index: int
    completed: bool = False
    quiz_score: Optional[int] = None # 0-5

class CourseProgressResponse(BaseModel):
    id: UUID
    course_id: UUID
    status: str # 'Yet To Start', 'In Progress', 'Completed'
    last_accessed_at: datetime

# --- 2. Feedback ---
class FeedbackCreate(BaseModel):
    chapter_id: UUID
    slide_index: Optional[int] = None
    is_positive: bool
    feedback_text: Optional[str] = None

# --- 3. Bookmarks ---
class BookmarkCreate(BaseModel):
    chapter_id: UUID
    slide_index: int
    note: Optional[str] = None

class BookmarkResponse(BaseModel):
    id: UUID
    chapter_id: UUID
    slide_index: int
    note: Optional[str]
    created_at: datetime

# --- 4. Daily Capsules ---
class DailyCapsuleResponse(BaseModel):
    id: UUID
    content: dict # JSON content
    date: datetime
    is_completed: bool

# --- 5. User Skills ---
class UserSkillResponse(BaseModel):
    skill_name: str
    level: int
