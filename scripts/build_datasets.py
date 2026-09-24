"""
Generates balanced 100 alumni + 100 students datasets.
Run: python scripts/build_datasets.py
"""
import pandas as pd
import random
import re
from datetime import datetime
from pathlib import Path

random.seed(42)

OUT_ALUMNI   = Path("data/alumni_clean.csv")
OUT_STUDENTS = Path("data/students_clean.csv")

SHARED_COLS = [
    "id","name","email","roll_number","role","branch","degree",
    "graduation_year","location","skills","interests","projects",
    "certifications","career_goal","target_role","target_industry",
    "bio","career_journey","is_synthetic","synthetic_fields",
    "profile_completeness","updated_at",
]

FIRST_NAMES = [
    "Karan","Sneha","Arjun","Riya","Neha","Anjali","Vikram","Amit","Rahul","Priya",
    "Aditya","Pooja","Rohit","Kavya","Siddharth","Divya","Manish","Shreya","Nikhil","Ananya",
    "Harsha","Meera","Varun","Isha","Rohan","Tanya","Yash","Nidhi","Karthik","Deepika",
    "Akash","Swati","Pranav","Aishwarya","Vivek","Rashmi","Naveen","Lakshmi","Abhishek","Preeti",
    "Gaurav","Sakshi","Rajat","Anita","Suresh","Rekha","Vinay","Neelam","Alok","Sunita",
]
LAST_NAMES = [
    "Sharma","Verma","Reddy","Rao","Patel","Kumar","Singh","Gupta","Nair","Iyer",
    "Menon","Joshi","Desai","Kulkarni","Chatterjee","Banerjee","Mukherjee","Das","Bose","Sen",
]

BRANCHES_TECH = [
    "Computer Science and Engineering","Information Technology",
    "Electronics and Communication Engineering","CSE (AI)","CSE (Data Science)",
    "CSE (Cyber Security)","CSE (IoT)","Mechanical Engineering","Electrical Engineering",
    "Civil Engineering","Mechatronics","BCA",
]

COMPANIES = {
    "TCS":       ("IT Services",         ["Python","Java","Git","DSA","REST APIs","SQL"]),
    "Infosys":   ("IT Services",         ["Python","Java","Git","DSA","REST APIs","Linux"]),
    "Wipro":     ("IT Services",         ["Python","Java","Git","DSA","REST APIs","SQL"]),
    "Amazon":    ("E-commerce / Cloud",  ["Python","C++","DSA","System Design","AWS","Docker"]),
    "Microsoft": ("Software / Cloud",    ["JavaScript","React","Node.js","Git","SQL","Azure"]),
    "Google":    ("Software / Internet", ["JavaScript","React","Node.js","Git","SQL","Golang"]),
}

INTERESTS_BY_INDUSTRY = {
    "IT Services":         "Enterprise Software, Consulting",
    "E-commerce / Cloud":  "Scalability, Cloud Architecture",
    "Software / Cloud":    "Platform Engineering, DevOps",
    "Software / Internet": "Search, Large Scale Systems",
}

SKILLS_BY_BRANCH = {
    "Computer Science and Engineering": ["Python","C","DSA","DBMS"],
    "Information Technology":           ["Python","Java","SQL","Git"],
    "Electronics and Communication Engineering": ["Signals","Embedded","C"],
    "CSE (AI)":                         ["Python","Machine Learning","Math","NumPy"],
    "CSE (Data Science)":               ["Python","Pandas","SQL","Statistics"],
    "CSE (Cyber Security)":             ["Networking","Linux","Python"],
    "CSE (IoT)":                        ["C++","Embedded","Python"],
    "Mechanical Engineering":           ["AutoCAD","Thermodynamics","SolidWorks"],
    "Electrical Engineering":           ["Circuits","Power Systems","MATLAB"],
    "Civil Engineering":                ["AutoCAD","Surveying","STAAD"],
    "Mechatronics":                     ["Robotics","Embedded","C++"],
    "BCA":                              ["Python","Web Development","SQL"],
}

INTERESTS_BY_BRANCH = {
    "Computer Science and Engineering": "Software Development, Problem Solving",
    "Information Technology":           "Web Development, Cloud",
    "Electronics and Communication Engineering": "Signal Processing, Embedded Systems",
    "CSE (AI)":                         "Artificial Intelligence, Deep Learning",
    "CSE (Data Science)":               "Analytics, Big Data",
    "CSE (Cyber Security)":             "Ethical Hacking, Networks",
    "CSE (IoT)":                        "Smart Devices, Sensors",
    "Mechanical Engineering":           "Manufacturing, Automotive",
    "Electrical Engineering":           "Power Systems, Renewables",
    "Civil Engineering":                "Infrastructure, Urban Planning",
    "Mechatronics":                     "Robotics, Automation",
    "BCA":                              "Full Stack Development, Databases",
}

GOAL_BY_BRANCH = {
    "Computer Science and Engineering": "Software Engineer",
    "Information Technology":           "Software Developer",
    "Electronics and Communication Engineering": "Embedded Engineer",
    "CSE (AI)":                         "AI/ML Engineer",
    "CSE (Data Science)":               "Data Scientist",
    "CSE (Cyber Security)":             "Security Engineer",
    "CSE (IoT)":                        "IoT Engineer",
    "Mechanical Engineering":           "Mechanical Design Engineer",
    "Electrical Engineering":           "Electrical Engineer",
    "Civil Engineering":                "Civil Engineer",
    "Mechatronics":                     "Mechatronics Engineer",
    "BCA":                              "Web Developer",
}

LOCATIONS = ["Hyderabad","Bangalore","Chennai","Delhi","Pune","Mumbai"]

def slug(name):
    s = name.lower().split()[0]
    return re.sub(r"[^a-z0-9]", "", s) or "user"

def today():
    return datetime.utcnow().strftime("%Y-%m-%d")

def pick_name(i):
    return f"{FIRST_NAMES[i % len(FIRST_NAMES)]} {LAST_NAMES[(i*3) % len(LAST_NAMES)]}"

# ---------- ALUMNI ----------
def build_alumni():
    rows = []
    for i in range(100):
        name     = pick_name(i)
        company  = list(COMPANIES.keys())[i % len(COMPANIES)]
        industry, skills = COMPANIES[company]
        branch   = BRANCHES_TECH[i % len(BRANCHES_TECH)]
        degree   = "B.Tech" if i % 3 else "M.Tech"
        grad_year = 2015 + (i % 9)
        years_exp = 2026 - grad_year
        loc = LOCATIONS[i % len(LOCATIONS)]
        rid = i + 1
        roll = f"AL{grad_year}{rid:04d}"
        email = f"{slug(name)}.{roll.lower()}@hitam.org"

        interests = INTERESTS_BY_INDUSTRY[industry]
        projects = f"Built a {random.choice(['analytics','payments','search','logging'])} dashboard used by {random.randint(5,30)} users"
        role_map = {
            "IT Services": "Software Engineer",
            "E-commerce / Cloud": "Software Development Engineer",
            "Software / Cloud": "Software Developer",
            "Software / Internet": "Software Developer",
        }
        current_role = role_map.get(industry, "Software Engineer")
        bio = (f"{current_role} at {company} ({degree} {branch}, class of {grad_year}). "
               f"{years_exp} years in {industry}. Based in {loc}.")
        journey = f"{grad_year} → Graduated | Joined {company} as {current_role} | {years_exp} yrs experience"
        completeness = round(min(1.0, 0.6 + 0.05 * len(skills)), 2)

        rows.append({
            "id": rid, "name": name, "email": email, "roll_number": roll,
            "role": "ALUMNI", "branch": branch, "degree": degree,
            "graduation_year": grad_year, "location": loc,
            "skills": ", ".join(skills), "interests": interests,
            "projects": projects, "certifications": "",
            "career_goal": current_role, "target_role": current_role,
            "target_industry": industry, "bio": bio, "career_journey": journey,
            "is_synthetic": "True",
            "synthetic_fields": "skills,interests,projects,bio,career_journey",
            "profile_completeness": completeness, "updated_at": today(),
        })
    df = pd.DataFrame(rows)[SHARED_COLS]
    OUT_ALUMNI.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_ALUMNI, index=False)
    print(f"[OK] Wrote {len(df)} alumni to {OUT_ALUMNI}")

# ---------- STUDENTS ----------
def build_students():
    rows = []
    for i in range(100):
        name = pick_name(i + 50)
        branch = BRANCHES_TECH[i % len(BRANCHES_TECH)]
        degree = "BCA" if branch == "BCA" else "B.Tech"
        admission_year = 2022
        grad_year = admission_year + 4
        rid = i + 1
        roll = f"{str(admission_year)[-2:]}{branch.split()[0][:3].upper()}{rid:04d}"
        email = f"{slug(name)}.{roll.lower()}@hitam.org"

        skills = SKILLS_BY_BRANCH.get(branch, ["Python","Git"])
        interests = INTERESTS_BY_BRANCH.get(branch, "Technology")
        goal = GOAL_BY_BRANCH.get(branch, "Software Engineer")
        loc = "Hyderabad"
        bio = (f"Year 2 {degree} {branch} student at HITAM. Aspiring {goal}. "
               f"Interested in {interests}.")
        journey = f"{admission_year} → Admitted | Year 2 | Expected graduation {grad_year}"
        completeness = round(min(1.0, 0.5 + 0.05 * len(skills)), 2)

        rows.append({
            "id": rid, "name": name, "email": email, "roll_number": roll,
            "role": "STUDENT", "branch": branch, "degree": degree,
            "graduation_year": grad_year, "location": loc,
            "skills": ", ".join(skills), "interests": interests,
            "projects": "", "certifications": "",
            "career_goal": goal, "target_role": goal,
            "target_industry": "Technology", "bio": bio, "career_journey": journey,
            "is_synthetic": "True",
            "synthetic_fields": "skills,interests,career_goal,target_role,bio,career_journey",
            "profile_completeness": completeness, "updated_at": today(),
        })
    df = pd.DataFrame(rows)[SHARED_COLS]
    OUT_STUDENTS.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_STUDENTS, index=False)
    print(f"[OK] Wrote {len(df)} students to {OUT_STUDENTS}")

if __name__ == "__main__":
    Path("data").mkdir(exist_ok=True)
    build_alumni()
    build_students()
    print("\nDone. Check your data/ folder.")