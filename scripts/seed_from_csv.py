import ast
import csv
import json
import re
from pathlib import Path

from app.auth import get_password_hash
from app.database import Base, SessionLocal, engine
from app.models import AlumniProfile, DatasetImport, Opportunity, StudentProfile, User

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

OPPORTUNITIES = [
    ("AI Engineering Intern", "Microsoft", "Build evaluation tools for applied ML teams.", ["Python", "Machine Learning"], "Internship", "2026-10-30", "Hyderabad · Hybrid", "https://careers.microsoft.com"),
    ("Data Science Challenge", "HITAM Innovation Cell", "A 48-hour campus sprint for data-led product ideas.", ["SQL", "Pandas"], "Challenge", "2026-10-12", "Campus · 48 hours", "https://hitam.org"),
    ("Women in Tech Fellowship", "Atlassian", "A guided fellowship for analytics and product builders.", ["Analytics", "Product"], "Fellowship", "2026-11-04", "Remote · India", "https://www.atlassian.com/company/careers"),
    ("Cloud Native Launchpad", "AWS", "Ship a production-ready service with cloud mentors.", ["Docker", "Cloud", "Python"], "Fellowship", "2026-11-18", "Remote · India", "https://aws.amazon.com/careers"),
    ("Open Source Maintainer Sprint", "GitHub", "Contribute to a real repository and earn maintainer feedback.", ["Git", "JavaScript", "Open Source"], "Challenge", "2026-10-22", "Remote · Global", "https://education.github.com"),
    ("Product Analytics Apprentice", "Flipkart", "Turn user behavior into decisions with a product analytics team.", ["SQL", "Analytics", "Product"], "Internship", "2026-12-02", "Bengaluru · Hybrid", "https://www.flipkartcareers.com"),
]


def list_value(value):
    if not value:
        return []
    value = str(value).strip()
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except (ValueError, SyntaxError):
        pass
    return [item.strip() for item in value.replace("|", ",").split(",") if item.strip()]


def integer_value(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def float_value(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0


def text_value(value):
    return str(value or "").strip()


def alumni_company(row):
    source = f"{text_value(row.get('bio'))} {text_value(row.get('career_journey'))}"
    match = re.search(r"\bat\s+(.+?)\s+\(", source)
    if not match:
        match = re.search(r"Joined\s+(.+?)\s+as\s+", source)
    return match.group(1).strip() if match else None


def alumni_experience(row):
    source = f"{text_value(row.get('bio'))} {text_value(row.get('career_journey'))}"
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*(?:in|experience)", source, re.IGNORECASE)
    return float(match.group(1)) if match else 0


def seed_profile(row, db):
    email = row["email"].strip().lower()
    if not email.endswith("@hitam.org"):
        return False
    role = row["role"].strip().upper()
    user = db.query(User).filter(User.email == email).first()
    is_new = user is None
    if is_new:
        user = User(email=email, hashed_password=get_password_hash("12345"), role=role,
                    must_change_password=True, is_active=True)
        db.add(user)
        db.flush()
    else:
        user.role = role
        user.is_active = True
    common = {
        "name": row.get("name"),
        "branch": row.get("branch"),
        "degree": row.get("degree"),
        "graduation_year": integer_value(row.get("graduation_year")),
        "location": row.get("location"),
        "skills": list_value(row.get("skills")),
        "interests": list_value(row.get("interests")),
        "projects": list_value(row.get("projects")),
        "certifications": list_value(row.get("certifications")),
        "bio": row.get("bio"),
        "is_synthetic": str(row.get("is_synthetic", "True")).lower() == "true",
        "synthetic_fields": list_value(row.get("synthetic_fields")),
        "profile_completeness": float_value(row.get("profile_completeness")),
    }
    if role == "ALUMNI":
        profile = user.alumni_profile or AlumniProfile(user_id=user.id)
        profile.alumni_id = row.get("id") or row.get("roll_number") or email.split("@")[0]
        profile.current_role = row.get("target_role")
        profile.company = alumni_company(row)
        profile.industry = row.get("target_industry")
        profile.years_experience = alumni_experience(row)
        profile.mentorship_expertise = common["skills"]
        profile.mentorship_available = True
        profile.career_journey = list_value(row.get("career_journey"))
        for key in {"name", "branch", "degree", "graduation_year", "location", "skills", "projects", "certifications", "bio", "is_synthetic", "synthetic_fields", "profile_completeness"}:
            setattr(profile, key, common[key])
        if is_new:
            db.add(profile)
    else:
        profile = user.student_profile or StudentProfile(user_id=user.id)
        profile.roll_number = row.get("roll_number")
        profile.career_goal = row.get("career_goal")
        profile.target_role = row.get("target_role")
        profile.target_industry = row.get("target_industry")
        for key in {"name", "branch", "degree", "graduation_year", "location", "skills", "projects", "certifications", "interests", "bio", "is_synthetic", "synthetic_fields", "profile_completeness"}:
            setattr(profile, key, common[key])
        if is_new:
            db.add(profile)
    return is_new


def seed_from_csv():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == "admin@hitam.org").first():
            db.add(User(email="admin@hitam.org", hashed_password=get_password_hash("Admin@123"),
                        role="ADMIN", must_change_password=False, is_active=True))
            db.commit()
        total = 0
        for filename in ("alumni_clean.csv", "students_clean.csv"):
            path = DATA_DIR / filename
            if not path.exists():
                continue
            imported_from_file = 0
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    imported = int(seed_profile(row, db))
                    total += imported
                    imported_from_file += imported
            db.add(DatasetImport(filename=filename, row_count=imported_from_file, source="prepared_csv", is_synthetic=True))
        existing_titles = {item.title for item in db.query(Opportunity).all()}
        for title, organization, description, skills, kind, deadline, location, link in OPPORTUNITIES:
            if title not in existing_titles:
                db.add(Opportunity(title=title, organization=organization, description=description,
                                   skills=skills, type=kind, deadline=deadline, location=location, link=link,
                                   experience_level="Student / Early career"))
        db.commit()
        print(f"Imported {total} prepared dataset records.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_from_csv()
