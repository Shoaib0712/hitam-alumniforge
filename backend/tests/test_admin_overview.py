from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_admin_analytics_returns_all_students_and_alumni():
    login = client.post(
        "/auth/login",
        json={"email": "admin@hitam.org", "password": "Admin@123"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    response = client.get(
        "/admin/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["summary"]["total_students"] >= 100
    assert payload["summary"]["total_alumni"] >= 100
    assert len(payload["students"]) >= 100
    assert len(payload["alumni"]) >= 100
    assert payload["students"][0]["skills"] is not None
    assert payload["alumni"][0]["skills"] is not None
