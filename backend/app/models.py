import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    must_change_password = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    alumni_profile = relationship("AlumniProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    roll_number = Column(String, unique=True, index=True)
    name = Column(String)
    branch = Column(String)
    degree = Column(String)
    admission_year = Column(Integer)
    graduation_year = Column(Integer)
    current_year = Column(Integer)
    cgpa = Column(Float)
    skills = Column(JSON, default=list)
    projects = Column(JSON, default=list)
    certifications = Column(JSON, default=list)
    career_goal = Column(String)
    target_role = Column(String)
    target_industry = Column(String)
    interests = Column(JSON, default=list)
    location = Column(String)
    bio = Column(Text)
    verified_status = Column(String, default="Platform Verified")
    is_synthetic = Column(Boolean, default=True)
    synthetic_fields = Column(JSON, default=list)
    profile_completeness = Column(Float, default=0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="student_profile")

class AlumniProfile(Base):
    __tablename__ = "alumni_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    alumni_id = Column(String, unique=True, index=True)
    roll_number = Column(String)
    name = Column(String)
    branch = Column(String)
    degree = Column(String)
    graduation_year = Column(Integer)
    company = Column(String)
    current_role = Column(String)
    industry = Column(String)
    years_experience = Column(Float)
    skills = Column(JSON, default=list)
    certifications = Column(JSON, default=list)
    location = Column(String)
    previous_companies = Column(JSON, default=list)
    projects = Column(JSON, default=list)
    mentorship_expertise = Column(JSON, default=list)
    mentorship_available = Column(Boolean, default=True)
    career_journey = Column(JSON, default=list)
    linkedin = Column(String)
    bio = Column(Text)
    verified_status = Column(String, default="Platform Verified")
    is_synthetic = Column(Boolean, default=True)
    synthetic_fields = Column(JSON, default=list)
    profile_completeness = Column(Float, default=0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="alumni_profile")

class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    organization = Column(String)
    description = Column(Text)
    skills = Column(JSON, default=list)
    location = Column(String)
    type = Column(String)
    deadline = Column(String)
    link = Column(String)
    experience_level = Column(String)

class MentorshipRequest(Base):
    __tablename__ = "mentorship_requests"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    alumni_id = Column(Integer, ForeignKey("users.id"))
    skill = Column(String)
    message = Column(Text)
    status = Column(String, default="Pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Connection(Base):
    __tablename__ = "connections"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    alumni_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="Pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SavedOpportunity(Base):
    __tablename__ = "saved_opportunities"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alumni_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feedback = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class DatasetImport(Base):
    __tablename__ = "dataset_imports"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    source = Column(String, default="prepared_csv")
    row_count = Column(Integer, default=0)
    is_synthetic = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    from sqlalchemy import Column, Integer, String, ForeignKey
from .database import Base

class MentorshipSession(Base):
    __tablename__ = "mentorship_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    alumni_id = Column(Integer, ForeignKey("users.id"))
    topic = Column(String, index=True)
    status = Column(String, default="PENDING")  # PENDING, APPROVED, REJECTED, COMPLETED
    scheduled_date = Column(String)