from app.database import SessionLocal
from app.auth import verify_password


def test_demo_and_csv_credentials_are_valid():
    db = SessionLocal()
    try:
        assert db.query(db.bind.execute("SELECT 1").__class__).count() >= 0
        demo_checks = {
            "admin@hitam.org": "Admin@123",
            "rahul@hitam.org": "230101",
            "vikram.alumni@hitam.org": "ALUM2020",
        }
        for email, password in demo_checks.items():
            user = db.query(__import__('app.models', fromlist=['User']).User).filter_by(email=email).first()
            assert user is not None, f"Missing demo user: {email}"
            assert verify_password(password, user.hashed_password), f"Wrong password for {email}"

        csv_user = db.query(__import__('app.models', fromlist=['User']).User).filter_by(email='karan.22com0001@hitam.org').first()
        assert csv_user is not None, "CSV dataset user missing from DB"
        assert verify_password('12345', csv_user.hashed_password), "CSV dataset password should be 12345"
    finally:
        db.close()
