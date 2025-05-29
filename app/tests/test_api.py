import sys
import os
from datetime import date, time
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from fastapi.testclient import TestClient
from main import app
import pytest
from crud import create_user
from schemas import UserCreate
from database import SessionLocal

client = TestClient(app)

@pytest.fixture
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def admin_token(db):
    # Create admin user
    admin = UserCreate(
        email="admin@test.com",
        password="admin123",
        name="Admin User",
        age=30,
        gender="other",
        is_admin=True
    )
    create_user(db, admin)
    
    # Get token
    response = client.post("/api/v1/auth/token", data={
        "username": admin.email,
        "password": admin.password
    })
    return response.json()["access_token"]

@pytest.fixture
def normal_token(db):
    # Create normal user
    user = UserCreate(
        email="user@test.com",
        password="user123",
        name="Normal User",
        age=25,
        gender="other",
        is_admin=False
    )
    create_user(db, user)
    
    # Get token
    response = client.post("/api/v1/auth/token", data={
        "username": user.email,
        "password": user.password
    })
    return response.json()["access_token"]

def test_docs_available():
    response = client.get("/docs")
    assert response.status_code == 200

def test_openapi_available():
    response = client.get("/openapi.json")
    assert response.status_code == 200

def test_register_user():
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "test123",
        "name": "Test User",
        "age": 25,
        "gender": "other",
        "is_admin": False
    })
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

def test_login():
    response = client.post("/api/v1/auth/token", data={
        "username": "test@example.com",
        "password": "test123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_create_room_admin(admin_token):
    response = client.post(
        "/api/v1/rooms/",
        json={
            "name": "Test Room",
            "room_type": "private",
            "capacity": 1
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Room"

def test_create_room_unauthorized(normal_token):
    response = client.post(
        "/api/v1/rooms/",
        json={
            "name": "Test Room",
            "room_type": "private",
            "capacity": 1
        },
        headers={"Authorization": f"Bearer {normal_token}"}
    )
    assert response.status_code == 403

def test_create_room_normal_user(normal_token):
    response = client.post(
        "/api/v1/rooms/",
        json={
            "name": "Test Room",
            "room_type": "private",
            "capacity": 1
        },
        headers={"Authorization": f"Bearer {normal_token}"}
    )
    assert response.status_code == 403

def test_book_room(normal_token, admin_token):
    # First create a room as admin
    room_response = client.post(
        "/api/v1/rooms/",
        json={
            "name": "Bookable Room",
            "room_type": "private",
            "capacity": 1
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert room_response.status_code == 200
    
    # Then try to book it as normal user
    booking_response = client.post(
        "/api/v1/bookings/",
        json={
            "slot_date": str(date.today()),
            "slot_start": str(time(9, 0)),
            "slot_end": str(time(10, 0)),
            "room_type": "private"
        },
        headers={"Authorization": f"Bearer {normal_token}"}
    )
    assert booking_response.status_code == 200

def test_book_shared_room(normal_token):
    # First create a shared room as admin
    admin_response = client.post(
        "/api/v1/rooms/",
        json={
            "name": "Shared Room",
            "room_type": "shared",
            "capacity": 4
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_response.status_code == 200
    room_id = admin_response.json()["id"]

    # Book shared room as normal user
    response = client.post(
        "/api/v1/bookings/",
        json={
            "room_id": room_id,
            "slot_date": str(date.today()),
            "slot_start": "09:00",
            "slot_end": "10:00"
        },
        headers={"Authorization": f"Bearer {normal_token}"}
    )
    assert response.status_code == 200
    booking_id = response.json()["id"]

    # Try to cancel booking
    cancel_response = client.delete(
        f"/api/v1/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {normal_token}"}
    )
    assert cancel_response.status_code == 200

def test_team_booking(normal_token, db):
    # Create a team
    team_response = client.post(
        "/api/v1/teams/",
        json={
            "name": "Test Team",
            "members": ["test@example.com", "user@test.com"]
        },
        headers={"Authorization": f"Bearer {normal_token}"}
    )
    assert team_response.status_code == 200
    team_id = team_response.json()["id"]

    # Book conference room for team
    response = client.post(
        "/api/v1/bookings/",
        json={
            "room_type": "conference",
            "team_id": team_id,
            "slot_date": str(date.today()),
            "slot_start": "14:00",
            "slot_end": "15:00"
        },
        headers={"Authorization": f"Bearer {normal_token}"}
    )
    assert response.status_code == 400  # Should fail as team size < 3

def test_double_booking_prevention(normal_token):
    # First booking
    response1 = client.post(
        "/api/v1/bookings/",
        json={
            "room_type": "private",
            "slot_date": str(date.today()),
            "slot_start": "11:00",
            "slot_end": "12:00"
        },
        headers={"Authorization": f"Bearer {normal_token}"}
    )
    assert response1.status_code == 200

    # Try to book overlapping slot
    response2 = client.post(
        "/api/v1/bookings/",
        json={
            "room_type": "private",
            "slot_date": str(date.today()),
            "slot_start": "11:30",
            "slot_end": "12:30"
        },
        headers={"Authorization": f"Bearer {normal_token}"}
    )
    assert response2.status_code == 400
