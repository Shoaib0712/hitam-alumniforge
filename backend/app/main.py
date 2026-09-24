from fastapi import Body, FastAPI, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import io
import os
import sys
from pathlib import Path

from .database import get_db, engine, ensure_schema
from .models import (
    Base, User, StudentProfile, AlumniProfile, Opportunity, MentorshipRequest,
    MentorshipSession, Connection, SavedOpportunity, RecommendationFeedback,
    Notification, DatasetImport, ChatMessage
)
from .ml import (
    calculate_alumni_matches, 
    generate_institutional_analytics, 
    build_alumni_network_graph,
    predict_placement_probability,
    cluster_alumni_skills,
    predict_career_trajectory,
    generate_pdf_report
)
from .auth import verify_password, get_password_hash, create_access_token, get_current_user, SECRET_KEY, ALGORITHM
from .schemas import (
    RegisterRequest, PasswordChangeRequest, MentorshipCreate, ConnectionCreate,
    RecommendationFeedbackCreate, ChatMessageCreate
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

# Initialize FastAPI application
app = FastAPI(title="HITAM AlumniForge API - Advanced Capstone", version="4.0")

# Configure CORS for Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip() for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:5175,http://localhost:5175"
        ).split(",") if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create SQLite database tables on startup
ensure_schema()
Base.metadata.create_all(bind=engine)
try:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from scripts.seed_from_csv import seed_from_csv
    seed_from_csv()
except Exception as seed_error:
    print(f"Dataset seed skipped: {seed_error}")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@app.get("/")
def read_root():
    return {"message": "HITAM AlumniForge Advanced Data Science Capstone Backend is running live!"}

@app.get("/platform/data-mode")
def platform_data_mode(db: Session = Depends(get_db)):
    imports = db.query(DatasetImport).order_by(DatasetImport.created_at.desc()).all()
    has_live = any(not item.is_synthetic for item in imports)
    return {
        "mode": "live" if has_live else "synthetic",
        "label": "Live Institutional Dataset" if has_live else "Synthetic Dataset",
        "imports": [{"filename": item.filename, "row_count": item.row_count, "is_synthetic": item.is_synthetic}
                    for item in imports[:10]]
    }

@app.post("/assistant/query")
def assistant_query(payload: AssistantQuery, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    question = payload.question.strip().lower()
    if not question:
        raise HTTPException(status_code=422, detail="Question is required.")
    if "missing" in question or "gap" in question:
        dna = career_dna(current_user)
        return {"intent": "skill_gaps", "answer": f"Your current profile has these evidence-based skill gaps: {', '.join(dna['missing_skills']) or 'No gaps detected yet.'}.", "cards": dna["missing_skills"]}
    if "mentor" in question or "help" in question:
        skill = next((word for word in payload.question.split() if len(word) > 3), "Python")
        cards = who_can_help(skill, current_user, db)
        return {"intent": "mentors", "answer": f"I found {len(cards)} alumni records associated with {skill}.", "cards": cards}
    if "opportun" in question:
        cards = list_opportunities(current_user, db)
        return {"intent": "opportunities", "answer": f"There are {len(cards)} opportunities in the current database.", "cards": cards}
    if "alumni" in question or "match" in question:
        cards = get_alumni_recommendations(current_user, db) if current_user.role == "STUDENT" else []
        return {"intent": "matches", "answer": f"I found {len(cards)} database-backed alumni matches for your profile.", "cards": cards[:10]}
    return {"intent": "profile", "answer": "Ask about alumni matches, missing skills, mentors, or opportunities so I can query your AlumniForge data.", "cards": []}

@app.get("/admin/data-quality")
def data_quality(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required.")
    issues = []
    for profile in db.query(StudentProfile).all():
        missing = [field for field, value in {"name": profile.name, "skills": profile.skills, "career_goal": profile.career_goal}.items() if not value]
        if missing:
            issues.append({"user_id": profile.user_id, "role": "STUDENT", "missing_fields": missing})
    for profile in db.query(AlumniProfile).all():
        missing = [field for field, value in {"name": profile.name, "skills": profile.skills, "company": profile.company, "graduation_year": profile.graduation_year}.items() if not value]
        if missing:
            issues.append({"user_id": profile.user_id, "role": "ALUMNI", "missing_fields": missing})
    return {"issue_count": len(issues), "issues": issues[:200], "status": "healthy" if not issues else "attention_needed"}

@app.get("/admin/analytics")
def admin_analytics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required.")

    students = db.query(StudentProfile).join(User).filter(User.is_active.is_(True)).all()
    alumni = db.query(AlumniProfile).join(User).filter(User.is_active.is_(True)).all()

    def normalize_list(value):
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(item).strip() for item in str(value).replace("|", ",").split(",") if str(item).strip()]

    all_skills = []
    for profile in students + alumni:
        all_skills.extend(normalize_list(getattr(profile, "skills", [])))

    student_rows = []
    for profile in sorted(students, key=lambda item: (item.name or "").lower()):
        student_rows.append({
            "user_id": profile.user_id,
            "email": profile.user.email if profile.user else None,
            "name": profile.name,
            "roll_number": profile.roll_number,
            "branch": profile.branch,
            "degree": profile.degree,
            "graduation_year": profile.graduation_year,
            "career_goal": profile.career_goal,
            "target_role": profile.target_role,
            "target_industry": profile.target_industry,
            "location": profile.location,
            "skills": normalize_list(profile.skills),
            "interests": normalize_list(profile.interests),
            "projects": normalize_list(profile.projects),
            "certifications": normalize_list(profile.certifications),
            "bio": profile.bio,
            "profile_completeness": profile.profile_completeness,
        })

    alumni_rows = []
    for profile in sorted(alumni, key=lambda item: (item.name or "").lower()):
        alumni_rows.append({
            "user_id": profile.user_id,
            "email": profile.user.email if profile.user else None,
            "name": profile.name,
            "alumni_id": profile.alumni_id,
            "branch": profile.branch,
            "degree": profile.degree,
            "graduation_year": profile.graduation_year,
            "company": profile.company,
            "current_role": profile.current_role,
            "industry": profile.industry,
            "years_experience": profile.years_experience,
            "location": profile.location,
            "skills": normalize_list(profile.skills),
            "mentorship_expertise": normalize_list(profile.mentorship_expertise),
            "projects": normalize_list(profile.projects),
            "certifications": normalize_list(profile.certifications),
            "career_journey": normalize_list(profile.career_journey),
            "bio": profile.bio,
            "profile_completeness": profile.profile_completeness,
        })

    return {
        "summary": {
            "total_users": len(students) + len(alumni),
            "total_students": len(students),
            "total_alumni": len(alumni),
            "total_skills": len(sorted(set(all_skills))),
            "active_connections": db.query(Connection).count(),
        },
        "students": student_rows,
        "alumni": alumni_rows,
    }

@app.get("/alumni")
def search_alumni(q: str = "", branch: str = "", industry: str = "", location: str = "", db: Session = Depends(get_db)):
    profiles = db.query(AlumniProfile).join(User).filter(User.is_active.is_(True)).all()
    def matches(profile):
        haystack = " ".join([profile.name or "", profile.company or "", profile.current_role or "", profile.industry or "", profile.branch or "", profile.location or "", " ".join(profile.skills or [])]).lower()
        return all(not value or value.lower() in haystack for value in [q, branch, industry, location])
    return [{"id": profile.user_id, "name": profile.name, "company": profile.company, "current_role": profile.current_role,
             "industry": profile.industry, "skills": profile.skills or [], "interests": profile.mentorship_expertise or [],
             "location": profile.location, "projects": profile.projects or [], "certifications": profile.certifications or [],
             "years_experience": profile.years_experience, "career_journey": profile.career_journey or [],
             "bio": profile.bio} for profile in profiles if matches(profile)]

@app.get("/students")
def search_students(q: str = "", branch: str = "", location: str = "", db: Session = Depends(get_db)):
    profiles = db.query(StudentProfile).join(User).filter(User.is_active.is_(True)).all()
    def matches(profile):
        haystack = " ".join([profile.name or "", profile.branch or "", profile.location or "", profile.career_goal or "",
                             profile.target_role or "", " ".join(profile.skills or [])]).lower()
        return all(not value or value.lower() in haystack for value in [q, branch, location])
    return [{"id": profile.user_id, "name": profile.name, "branch": profile.branch, "degree": profile.degree,
         "target_role": profile.target_role, "career_goal": profile.career_goal, "skills": profile.skills or [],
         "interests": profile.interests or [], "projects": profile.projects or [], "certifications": profile.certifications or [],
         "location": profile.location, "bio": profile.bio}
        for profile in profiles if matches(profile)]

# --- UNIVERSAL AUTHENTICATION ENDPOINT ---
@app.post("/auth/login")
async def login_for_access_token(request: Request, db: Session = Depends(get_db)):
    """Authenticates user credentials using a JSON payload with email and password."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    email = str(email).strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "must_change_password": getattr(user, "must_change_password", False)
    }

@app.post("/auth/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if not email.endswith("@hitam.org"):
        raise HTTPException(status_code=400, detail="Registration is limited to @hitam.org addresses.")
    if payload.role not in {"STUDENT", "ALUMNI"}:
        raise HTTPException(status_code=400, detail="Only student and alumni accounts can self-register.")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must contain at least 8 characters.")
    user = User(email=email, hashed_password=get_password_hash(payload.password), role=payload.role, must_change_password=False)
    db.add(user)
    db.flush()
    if payload.role == "STUDENT":
        db.add(StudentProfile(user_id=user.id, name=payload.name, roll_number=payload.roll_number,
                              branch=payload.branch, graduation_year=payload.graduation_year, skills=[],
                              interests=[]))
    else:
        db.add(AlumniProfile(user_id=user.id, name=payload.name, alumni_id=payload.roll_number or email.split("@")[0],
                             branch=payload.branch, graduation_year=payload.graduation_year, skills=[],
                             mentorship_expertise=[]))
    db.commit()
    return {"message": "Account created successfully.", "user_id": user.id}

# --- CURRENT USER ENDPOINT ---
@app.get("/users/me")
def read_users_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns the profile of the currently authenticated user based on JWT token."""
    user = current_user
    profile = user.student_profile or user.alumni_profile
    display_name = getattr(profile, "name", None) or user.email.split("@")[0].capitalize()
        
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "name": display_name,
        "fullName": display_name,
        "username": display_name,
        "department": getattr(profile, "branch", None) or "Data Science",
        "must_change_password": user.must_change_password,
        "profile": {key: value for key, value in profile.__dict__.items() if not key.startswith("_")} if profile else {},
    }

@app.put("/users/me")
def update_users_me(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = current_user.student_profile or current_user.alumni_profile
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    allowed = {"name", "branch", "degree", "graduation_year", "location", "skills", "interests", "projects",
               "certifications", "career_goal", "target_role", "target_industry", "bio", "company", "current_role",
               "industry", "years_experience", "previous_companies", "mentorship_expertise", "mentorship_available",
               "career_journey", "linkedin"}
    for key, value in payload.items():
        if key in allowed and hasattr(profile, key):
            setattr(profile, key, value)
    db.commit()
    return {"message": "Profile updated successfully."}

@app.post("/auth/change-password")
def change_password(payload: PasswordChangeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must contain at least 8 characters.")
    current_user.hashed_password = get_password_hash(payload.new_password)
    current_user.must_change_password = False
    db.commit()
    return {"message": "Password updated successfully."}

# --- RECOMMENDATIONS ENDPOINT ---
@app.get("/recommendations/alumni")
def get_alumni_recommendations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "STUDENT":
        raise HTTPException(status_code=403, detail="Only students receive alumni recommendations.")
    student = current_user.student_profile
    alumni = db.query(AlumniProfile).join(User).filter(User.is_active.is_(True)).all()
    student_text = " ".join((student.skills or []) + (student.interests or []) + [student.target_role or "", student.target_industry or "", student.career_goal or ""])
    results = []
    for profile in alumni:
        alumni_text = " ".join((profile.skills or []) + (profile.mentorship_expertise or []) + [profile.current_role or "", profile.industry or "", profile.company or ""])
        documents = [student_text or "career", alumni_text or "professional"]
        matrix = TfidfVectorizer(stop_words="english").fit_transform(documents)
        score = float(cosine_similarity(matrix[0:1], matrix[1:]).flatten()[0]) * 100
        overlap = sorted(set((student.skills or [])).intersection({item for item in (profile.skills or [])}))
        results.append({"alumni_id": profile.user_id, "name": profile.name, "current_role": profile.current_role,
                        "company": profile.company, "match_score": round(score, 2),
                        "matching_skills": overlap, "reason": "Shared skills and career direction from your profiles."})
    return sorted(results, key=lambda item: item["match_score"], reverse=True)

@app.get("/career-dna")
def career_dna(current_user: User = Depends(get_current_user)):
    profile = current_user.student_profile or current_user.alumni_profile
    if not profile:
        raise HTTPException(status_code=404, detail="Create a profile to generate Career DNA.")
    current_skills = profile.skills or []
    common_gaps = ["Docker", "MLOps", "Cloud deployment"]
    return {"primary_goal": getattr(profile, "target_role", None) or getattr(profile, "career_goal", None) or getattr(profile, "current_role", None) or "Explore your next role",
            "strong_skills": current_skills[:6], "missing_skills": [skill for skill in common_gaps if skill.lower() not in {item.lower() for item in current_skills}],
            "interests": getattr(profile, "interests", None) or [], "projects_count": len(getattr(profile, "projects", None) or [])}

@app.post("/mentorship/request")
def request_mentorship(payload: MentorshipCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "STUDENT":
        raise HTTPException(status_code=403, detail="Only students can request mentorship.")
    alumni = db.query(User).filter(User.id == payload.alumni_user_id, User.role == "ALUMNI", User.is_active.is_(True)).first()
    if not alumni:
        raise HTTPException(status_code=404, detail="Alumni profile not found.")
    existing = db.query(MentorshipRequest).filter(MentorshipRequest.student_id == current_user.id,
        MentorshipRequest.alumni_id == alumni.id, MentorshipRequest.status == "Pending").first()
    if existing:
        raise HTTPException(status_code=409, detail="A pending request already exists.")
    request = MentorshipRequest(student_id=current_user.id, alumni_id=alumni.id, skill=payload.skill, message=payload.message)
    db.add(request)
    db.add(Notification(user_id=alumni.id, title="New mentorship request", message=f"{current_user.email} requested help with {payload.skill}."))
    db.commit()
    return {"message": "Mentorship request sent successfully.", "request_id": request.id}

@app.post("/connections")
def create_connection(payload: ConnectionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "STUDENT":
        raise HTTPException(status_code=403, detail="Only students can send connection requests.")
    alumni = db.query(User).filter(User.id == payload.alumni_user_id, User.role == "ALUMNI").first()
    if not alumni:
        alumni_profile = db.query(AlumniProfile).filter(AlumniProfile.id == payload.alumni_user_id).first()
        alumni = alumni_profile.user if alumni_profile else None
    if not alumni:
        raise HTTPException(status_code=404, detail="Alumni profile not found.")
    connection = db.query(Connection).filter(Connection.student_id == current_user.id,
                                             Connection.alumni_id == alumni.id).first()
    if connection and connection.status not in {"Rejected"}:
        raise HTTPException(status_code=409, detail=f"Connection is already {connection.status.lower()}.")
    if connection:
        connection.status = "Pending"
    else:
        connection = Connection(student_id=current_user.id, alumni_id=alumni.id, status="Pending")
        db.add(connection)
    db.add(Notification(user_id=alumni.id, title="New connection request", message=f"{current_user.email} wants to connect."))
    db.commit()
    return {"message": "Connection request sent.", "connection_id": connection.id}

@app.post("/connections/request")
def request_connection_alias(payload: ConnectionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_connection(payload, current_user, db)

@app.get("/connections")
def list_connections(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.query(Connection).filter(
        (Connection.student_id == current_user.id) | (Connection.alumni_id == current_user.id)
    ).order_by(Connection.created_at.desc()).all()
    result = []
    for item in records:
        other_id = item.alumni_id if item.student_id == current_user.id else item.student_id
        other = db.query(User).filter(User.id == other_id).first()
        profile = (other.student_profile or other.alumni_profile) if other else None
        result.append({"id": item.id, "status": item.status, "other_user_id": other_id,
                       "name": getattr(profile, "name", other.email if other else "Unknown"),
                       "role": other.role if other else None})
    return result

def update_connection(connection_id: int, status: str, current_user: User, db: Session):
    connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if not connection or current_user.id not in {connection.student_id, connection.alumni_id}:
        raise HTTPException(status_code=404, detail="Connection request not found.")
    if current_user.id != connection.alumni_id:
        raise HTTPException(status_code=403, detail="Only the alumni recipient can respond.")
    connection.status = status
    recipient = connection.student_id
    db.add(Notification(user_id=recipient, title=f"Connection {status.lower()}",
                        message="Your connection request has been updated."))
    db.commit()
    return {"message": f"Connection {status.lower()}."}

@app.put("/connections/{connection_id}/accept")
def accept_connection(connection_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return update_connection(connection_id, "Connected", current_user, db)

@app.put("/connections/{connection_id}/reject")
def reject_connection(connection_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return update_connection(connection_id, "Rejected", current_user, db)

def get_connection_for_user(connection_id: int, current_user: User, db: Session):
    connection = db.query(Connection).filter(Connection.id == connection_id, Connection.status == "Connected").first()
    if not connection or current_user.id not in {connection.student_id, connection.alumni_id}:
        raise HTTPException(status_code=404, detail="An accepted connection is required to use chat.")
    return connection

@app.get("/connections/{connection_id}/messages")
def list_messages(connection_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_connection_for_user(connection_id, current_user, db)
    return [{"id": item.id, "sender_id": item.sender_id, "message": item.message,
             "created_at": item.created_at.isoformat()} for item in db.query(ChatMessage)
            .filter(ChatMessage.connection_id == connection_id).order_by(ChatMessage.created_at.asc()).all()]

@app.post("/connections/{connection_id}/messages")
def send_message(connection_id: int, payload: ChatMessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    connection = get_connection_for_user(connection_id, current_user, db)
    message = payload.message.strip()
    if not message or len(message) > 2000:
        raise HTTPException(status_code=422, detail="Message must contain 1-2000 characters.")
    recipient = connection.alumni_id if connection.student_id == current_user.id else connection.student_id
    record = ChatMessage(connection_id=connection_id, sender_id=current_user.id, message=message)
    db.add(record)
    db.add(Notification(user_id=recipient, title="New chat message", message="You received a new message in AlumniForge."))
    db.commit()
    db.refresh(record)
    return {"id": record.id, "sender_id": record.sender_id, "message": record.message, "created_at": record.created_at.isoformat()}

@app.post("/recommendations/feedback")
def recommendation_feedback(payload: RecommendationFeedbackCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.feedback not in {"HELPFUL", "NOT_RELEVANT", "INTERESTED", "DISMISSED"}:
        raise HTTPException(status_code=400, detail="Unsupported feedback value.")
    db.add(RecommendationFeedback(student_id=current_user.id, alumni_id=payload.alumni_id, feedback=payload.feedback))
    db.commit()
    return {"message": "Feedback recorded."}

def serialize_opportunity(item, saved=False):
    return {"id": item.id, "title": item.title, "organization": item.organization, "description": item.description,
            "skills": item.skills or [], "location": item.location, "type": item.type, "deadline": item.deadline,
            "link": item.link, "experience_level": item.experience_level, "saved": saved}

@app.get("/opportunities")
def list_opportunities(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    saved_ids = {row.opportunity_id for row in db.query(SavedOpportunity).filter(SavedOpportunity.user_id == current_user.id).all()}
    profile = current_user.student_profile or current_user.alumni_profile
    profile_skills = {item.lower() for item in (profile.skills or [])} if profile else set()
    result = []
    for item in db.query(Opportunity).order_by(Opportunity.id.desc()).all():
        overlap = [skill for skill in (item.skills or []) if skill.lower() in profile_skills]
        card = serialize_opportunity(item, item.id in saved_ids)
        card["fit_score"] = min(99, 45 + len(overlap) * 18)
        card["matching_skills"] = overlap
        result.append(card)
    return sorted(result, key=lambda item: (-item["fit_score"], item["id"]))

@app.post("/opportunities/{opportunity_id}/save")
def save_opportunity(opportunity_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    existing = db.query(SavedOpportunity).filter(SavedOpportunity.user_id == current_user.id,
                                                   SavedOpportunity.opportunity_id == opportunity_id).first()
    if not existing:
        db.add(SavedOpportunity(user_id=current_user.id, opportunity_id=opportunity_id))
        db.commit()
    return {"message": "Opportunity saved to your launch list.", "opportunity_id": opportunity_id, "saved": True}

@app.delete("/opportunities/{opportunity_id}/save")
def unsave_opportunity(opportunity_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(SavedOpportunity).filter(SavedOpportunity.user_id == current_user.id,
                                                   SavedOpportunity.opportunity_id == opportunity_id).first()
    if existing:
        db.delete(existing)
        db.commit()
    return {"message": "Opportunity removed from your launch list.", "opportunity_id": opportunity_id, "saved": False}

@app.get("/skills/who-can-help")
def who_can_help(skill: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    requested = skill.strip().lower()
    if not requested:
        raise HTTPException(status_code=422, detail="Skill is required.")
    profiles = db.query(AlumniProfile).join(User).filter(User.is_active.is_(True)).all()
    matches = []
    for profile in profiles:
        skills = (profile.skills or []) + (profile.mentorship_expertise or [])
        if any(requested in item.lower() for item in skills):
            matches.append({"alumni_id": profile.user_id, "name": profile.name, "company": profile.company,
                            "current_role": profile.current_role, "matching_skill": skill,
                            "mentorship_available": profile.mentorship_available})
    return matches

@app.post("/career/what-if")
def career_what_if(payload: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    skill = str(payload.get("new_skill", "")).strip()
    if not skill:
        raise HTTPException(status_code=422, detail="A new skill is required.")
    alumni = db.query(AlumniProfile).join(User).filter(User.is_active.is_(True)).all()
    comparable = [profile for profile in alumni if any(skill.lower() in item.lower() for item in (profile.skills or []))]
    co_skill_counts, role_counts = {}, {}
    for profile in comparable:
        for item in profile.skills or []:
            if item.lower() != skill.lower():
                co_skill_counts[item] = co_skill_counts.get(item, 0) + 1
        if profile.current_role:
            role_counts[profile.current_role] = role_counts.get(profile.current_role, 0) + 1
    opportunities = [item for item in db.query(Opportunity).all()
                      if any(skill.lower() in item_skill.lower() for item_skill in (item.skills or []))]
    return {
        "new_skill": skill,
        "evidence_note": "Comparable career trajectories observed in the available alumni data.",
        "comparable_alumni_count": len(comparable),
        "comparable_alumni": [{"name": item.name, "company": item.company, "role": item.current_role} for item in comparable[:10]],
        "common_co_skills": sorted(co_skill_counts, key=co_skill_counts.get, reverse=True)[:8],
        "related_roles": sorted(role_counts, key=role_counts.get, reverse=True)[:8],
        "opportunities_opened": [{"title": item.title, "organization": item.organization, "type": item.type} for item in opportunities[:10]],
        "mentors_available": sum(1 for item in comparable if item.mentorship_available),
    }

@app.get("/recommendations/students")
def get_student_recommendations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "ALUMNI":
        raise HTTPException(status_code=403, detail="Only alumni receive student recommendations.")
    alumni = current_user.alumni_profile
    expertise = set(item.lower() for item in ((alumni.skills or []) + (alumni.mentorship_expertise or [])))
    results = []
    for student in db.query(StudentProfile).join(User).filter(User.is_active.is_(True)).all():
        student_skills = set(item.lower() for item in (student.skills or []))
        overlap = sorted(expertise.intersection(student_skills))
        gaps = sorted(expertise - student_skills)
        score = min(99, round((len(overlap) * 20) + (len(gaps) * 3), 2))
        if overlap or student.target_role:
            results.append({"student_id": student.user_id, "name": student.name, "target_role": student.target_role,
                            "match_score": score, "shared_skills": overlap, "potential_help": gaps[:5]})
    return sorted(results, key=lambda item: item["match_score"], reverse=True)

@app.get("/mentorship/requests")
def mentorship_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    column = MentorshipRequest.student_id if current_user.role == "STUDENT" else MentorshipRequest.alumni_id
    records = db.query(MentorshipRequest).filter(column == current_user.id).order_by(MentorshipRequest.created_at.desc()).all()
    return [{"id": item.id, "student_id": item.student_id, "alumni_id": item.alumni_id, "skill": item.skill,
             "message": item.message, "status": item.status, "created_at": item.created_at.isoformat()} for item in records]

def update_mentorship_status(request_id: int, status: str, current_user: User, db: Session):
    record = db.query(MentorshipRequest).filter(MentorshipRequest.id == request_id).first()
    if not record or current_user.id not in {record.student_id, record.alumni_id}:
        raise HTTPException(status_code=404, detail="Mentorship request not found.")
    if current_user.id != record.alumni_id and status in {"Accepted", "Rejected"}:
        raise HTTPException(status_code=403, detail="Only the requested alumni can respond.")
    record.status = status
    recipient = record.student_id if current_user.id == record.alumni_id else record.alumni_id
    db.add(Notification(user_id=recipient, title=f"Mentorship request {status.lower()}",
                        message=f"Your mentorship request for {record.skill} is now {status.lower()}."))
    db.commit()
    return {"message": f"Mentorship request {status.lower()}."}

@app.put("/mentorship/{request_id}/accept")
def accept_mentorship(request_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return update_mentorship_status(request_id, "Accepted", current_user, db)

@app.put("/mentorship/{request_id}/reject")
def reject_mentorship(request_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return update_mentorship_status(request_id, "Rejected", current_user, db)

@app.put("/mentorship/{request_id}/complete")
def complete_mentorship(request_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return update_mentorship_status(request_id, "Completed", current_user, db)

@app.get("/notifications")
def notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(50).all()
    return [{"id": item.id, "title": item.title, "message": item.message, "is_read": item.is_read,
             "created_at": item.created_at.isoformat()} for item in records]

@app.put("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Notification not found.")
    record.is_read = True
    db.commit()
    return {"message": "Notification marked as read."}

@app.get("/admin/skills/intelligence")
def skills_intelligence(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required.")
    demand, expertise = {}, {}
    for profile in db.query(StudentProfile).all():
        for skill in profile.skills or []:
            demand[skill] = demand.get(skill, 0) + 1
    for profile in db.query(AlumniProfile).all():
        for skill in set((profile.skills or []) + (profile.mentorship_expertise or [])):
            expertise[skill] = expertise.get(skill, 0) + 1
    skills = sorted(set(demand) | set(expertise), key=lambda item: demand.get(item, 0), reverse=True)
    rows = []
    for skill in skills:
        student_count, alumni_count = demand.get(skill, 0), expertise.get(skill, 0)
        status = "COVERED" if alumni_count >= student_count else ("CRITICAL_GAP" if student_count >= 5 and alumni_count == 0 else "GAP")
        rows.append({"skill": skill, "student_demand": student_count, "alumni_expertise": alumni_count, "status": status})
    return {"skills": rows, "actions": [{"skill": row["skill"], "recommendation": "Alumni workshop / mentorship cohort"} for row in rows if row["status"] != "COVERED"][:10]}


# --- ADVANCED CAPSTONE / MAJOR PROJECT ENDPOINTS ---

class JobMatchRequest(BaseModel):
    resume_text: str
    job_description: str

class WhatIfRequest(BaseModel):
    new_skill: str

class AssistantQuery(BaseModel):
    question: str

@app.post("/api/match-job")
def match_resume_to_job(payload: JobMatchRequest):
    """AI Resume-to-Job Matcher utilizing NLP Cosine Similarity."""
    documents = [payload.resume_text, payload.job_description]
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    score = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()[0])
    match_pct = round(score * 100, 2)
    
    return {
        "match_score": match_pct,
        "feedback": "Strong technical alignment with job description requirements." if match_pct > 40 else "Gap detected: Consider adding more relevant framework keywords."
    }

@app.get("/api/analytics/dashboard")
def get_dashboard_analytics(db: Session = Depends(get_db)):
    """Institutional Analytics Engine powered by Pandas."""
    users = db.query(User).all()
    return generate_institutional_analytics(users)

@app.get("/api/network/graph-data")
def get_network_graph(db: Session = Depends(get_db)):
    """NetworkX Graph API mapping alumni corporate connections & centralities."""
    users = db.query(User).all()
    return build_alumni_network_graph(users)

class PlacementRequest(BaseModel):
    gpa: float
    projects_count: int
    coding_score: float

@app.get("/career/readiness")
def career_readiness(current_user: User = Depends(get_current_user)):
    profile = current_user.student_profile or current_user.alumni_profile
    if not profile:
        raise HTTPException(status_code=404, detail="Create a profile before calculating readiness.")
    projects = len(profile.projects or [])
    skills = profile.skills or []
    gpa = getattr(profile, "cgpa", None) or 7.5
    coding_score = min(100, 42 + (len(skills) * 7) + min(projects, 4) * 6)
    result = predict_placement_probability(float(gpa), projects, coding_score)
    result.update({
        "inputs": {"gpa": round(float(gpa), 2), "projects_count": projects, "coding_score": round(coding_score, 2)},
        "signals": {
            "gpa": round(min(100, float(gpa) / 10 * 100)),
            "portfolio": round(min(100, projects / 4 * 100)),
            "coding": round(coding_score)
        },
        "next_moves": [
            "Add one measurable project outcome." if projects < 3 else "Add deployment or scale metrics to your projects.",
            "Practice timed coding problems twice this week." if coding_score < 75 else "Keep your coding signal warm with one timed set weekly."
        ]
    })
    return result

@app.post("/api/ml/predict-placement")
def predict_placement(payload: PlacementRequest):
    """Machine Learning Placement Success Estimator."""
    return predict_placement_probability(payload.gpa, payload.projects_count, payload.coding_score)

@app.get("/api/ml/alumni-clusters")
def get_alumni_clusters(db: Session = Depends(get_db)):
    """Unsupervised K-Means Clustering of Alumni Profiles."""
    users = db.query(User).all()
    return cluster_alumni_skills(users)

class CareerTrajectoryRequest(BaseModel):
    skills: str
    experience_years: int

@app.post("/api/ml/career-trajectory")
def career_trajectory_prediction(payload: CareerTrajectoryRequest):
    """Random Forest Classifier Predicting Career Specialization."""
    return predict_career_trajectory(payload.skills, payload.experience_years)

@app.get("/api/analytics/export-csv")
def export_analytics_csv(db: Session = Depends(get_db)):
    """Pandas Data Pipeline generating downloadable institutional CSV reports."""
    users = db.query(User).all()
    df = pd.DataFrame([
        {
            "ID": u.id,
            "Email": u.email,
            "Role": u.role,
            "Department": getattr(u, "department", "Data Science"),
            "Company": getattr(u, "company", "Independent")
        } for u in users
    ])
    
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=hitam_alumni_analytics.csv"
    return response

@app.get("/api/analytics/export-pdf")
def export_analytics_pdf(db: Session = Depends(get_db)):
    """Automated ReportLab PDF Generator for Institutional Reviews."""
    users = db.query(User).all()
    pdf_buffer = generate_pdf_report(users)
    response = StreamingResponse(pdf_buffer, media_type="application/pdf")
    response.headers["Content-Disposition"] = "attachment; filename=hitam_institutional_report.pdf"
    return response

class MentorshipBooking(BaseModel):
    alumni_id: int
    topic: str
    scheduled_date: str

@app.post("/api/mentorship/book")
def book_mentorship_session(payload: MentorshipBooking, db: Session = Depends(get_db)):
    """Mentorship booking workflow endpoint."""
    session = MentorshipSession(
        student_id=1,
        alumni_id=payload.alumni_id,
        topic=payload.topic,
        scheduled_date=payload.scheduled_date,
        status="PENDING"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"message": "Mentorship session requested successfully", "session_id": session.id}

@app.on_event("startup")
def auto_seed_database():
    from app.database import SessionLocal
    from app.models import User
    from passlib.context import CryptContext
    
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.email == "admin@hitam.org").first()
        if not admin_user:
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            hashed_password = pwd_context.hash("Admin@123")
            
            new_admin = User(
                email="admin@hitam.org",
                hashed_password=hashed_password,
                role="admin",
                full_name="Admin User"
            )
            db.add(new_admin)
            db.commit()
            print("Default admin user created successfully!")
    except Exception as e:
        print(f"Seeding skipped or failed: {e}")
    finally:
        db.close()