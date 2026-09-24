import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hitam_alumniforge.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def ensure_schema():
    """Add lightweight columns for existing SQLite installs before create_all users rely on them."""
    additions = {
        "student_profiles": {
            "is_synthetic": "BOOLEAN DEFAULT 1",
            "synthetic_fields": "JSON",
            "profile_completeness": "FLOAT DEFAULT 0",
            "updated_at": "DATETIME",
        },
        "alumni_profiles": {
            "is_synthetic": "BOOLEAN DEFAULT 1",
            "synthetic_fields": "JSON",
            "profile_completeness": "FLOAT DEFAULT 0",
            "updated_at": "DATETIME",
        },
    }
    inspector = inspect(engine)
    with engine.begin() as connection:
        table_names = inspector.get_table_names()
        for table, columns in additions.items():
            # If the table doesn't exist yet, skip ALTER TABLE (create_all will build it fresh)
            if table not in table_names:
                continue
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, definition in columns.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()