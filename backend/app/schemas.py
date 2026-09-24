from pydantic import BaseModel
from typing import List, Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    must_change_password: bool

class StudentProfileUpdate(BaseModel):
    name: Optional[str] = None
    branch: Optional[str] = None
    degree: Optional[str] = None
    cgpa: Optional[float] = None
    skills: Optional[List[str]] = None
    career_goal: Optional[str] = None
    target_role: Optional[str] = None
    target_industry: Optional[str] = None
    interests: Optional[List[str]] = None
    location: Optional[str] = None
    bio: Optional[str] = None

class MentorshipCreate(BaseModel):
    alumni_user_id: int
    skill: str
    message: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str = "STUDENT"
    name: str
    roll_number: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[int] = None

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class ConnectionCreate(BaseModel):
    alumni_user_id: int

class RecommendationFeedbackCreate(BaseModel):
    alumni_id: int
    feedback: str

class ChatMessageCreate(BaseModel):
    message: str