from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from uuid import UUID

class ProfileCreate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class ProfileResponse(BaseModel):
    id: UUID
    full_name: Optional[str]
    avatar_url: Optional[str]
    current_streak: int
    total_xp: int
    created_at: datetime
