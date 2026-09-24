from app.database import SessionLocal, engine, Base
from app.models import User, StudentProfile, AlumniProfile, Opportunity
from app.auth import get_password_hash

Base.metadata.create_all(bind=engine)
def seed():
    db = SessionLocal()
    if db.query(User).count() > 0:
        return
    admin = User(email="admin@hitam.org", hashed_password=get_password_hash("Admin@123"), role="ADMIN", must_change_password=False)
    db.add(admin)
    s_user = User(email="rahul@hitam.org", hashed_password=get_password_hash("230101"), role="STUDENT", must_change_password=True)
    db.add(s_user)
    db.flush()
    s_profile = StudentProfile(user_id=s_user.id, roll_number="230101", name="Rahul Sharma", branch="Data Science", degree="B.Tech", graduation_year=2027, cgpa=8.8, skills=["Python", "Machine Learning", "SQL", "Pandas"], career_goal="Machine Learning Engineer")
    db.add(s_profile)
    a_user = User(email="vikram.alumni@hitam.org", hashed_password=get_password_hash("ALUM2020"), role="ALUMNI", must_change_password=True)
    db.add(a_user)
    db.flush()
    a_profile = AlumniProfile(user_id=a_user.id, alumni_id="ALUM2020", name="Vikram Reddy", branch="Data Science", graduation_year=2020, company="Microsoft", current_role="Senior ML Engineer", skills=["Python", "Machine Learning", "Docker", "MLOps"], mentorship_available=True)
    db.add(a_profile)
    opp = Opportunity(title="AI Engineering Intern", organization="Microsoft", description="Looking for passionate data science students.", skills=["Python", "Machine Learning"], type="Internship", deadline="2026-10-30", link="https://careers.microsoft.com")
    db.add(opp)
    db.commit()
    print("Seeded successfully!")
if __name__ == "__main__":
    seed()