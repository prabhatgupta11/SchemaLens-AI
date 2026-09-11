import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from db.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_list_datasets():
    response = client.get("/api/datasets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_upload_non_csv():
    response = client.post(
        "/api/datasets",
        files={"file": ("test.txt", b"some data", "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Only CSV files are supported"
