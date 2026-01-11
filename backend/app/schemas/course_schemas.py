from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

# --- Enums (defined as Literals for simplicity in Pydantic)
CourseDifficulty = str # 'Low', 'Medium', 'High'
CourseType = str # 'Interview', 'Basics', 'Deep Concepts'

# --- 1. Course Generation Request ---
class CourseGenerateRequest(BaseModel):
    topic: str = Field(..., max_length=100)
    difficulty: CourseDifficulty = Field(default="Medium")
    course_type: CourseType = Field(default="Basics")
    length: str = Field(default="Medium") # Short, Medium, Long check

# --- 2. TOC Structures (used in DB 'toc' column) ---
class TOCChapter(BaseModel):
    title: str
    shortDescription: str
    order: int

class CourseTOC(BaseModel):
    title: str
    description: str
    chapters: List[TOCChapter]

# --- 3. Chapter Content Structures (used in DB 'content' column) ---
class Slide(BaseModel):
    title: str
    content: str
    explainMore: str
    deeperConcepts: str
    quickExamples: str
    analogy: str

class QuizOption(BaseModel):
    question: str
    options: List[str]
    correctAnswer: str
    explanation: str

class ChapterContent(BaseModel):
    slides: List[Slide]
    quiz: List[QuizOption]

# --- 4. DB Response Models (For API Responses) ---
class CourseResponse(BaseModel):
    id: UUID
    title: str
    description: str
    difficulty: str
    course_type: str
    length: str
    toc: CourseTOC
    created_at: datetime

class ChapterGenerateRequest(BaseModel):
    course_id: UUID
    chapter_index: int

class ChapterResponse(BaseModel):
    id: UUID
    course_id: UUID
    chapter_index: int
    title: str
    content: Optional[ChapterContent] # slides + quiz
    is_generated: bool
    created_at: datetime
