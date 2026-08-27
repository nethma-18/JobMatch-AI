import pytest
from bson import ObjectId
from app.core.security import create_access_token

@pytest.fixture
def hr1_token():
    return create_access_token({"sub": "660000000000000000000010", "role": "hr"})

@pytest.fixture
def hr2_token():
    return create_access_token({"sub": "660000000000000000000011", "role": "hr"})

@pytest.fixture
def seeker_token():
    return create_access_token({"sub": "660000000000000000000012", "role": "seeker"})

@pytest.fixture(autouse=True)
def setup_users(mock_db):
    mock_db.sync_db["users"].insert_many([
        {"_id": ObjectId("660000000000000000000010"), "name": "HR One", "email": "hr1@test.com", "role": "hr", "is_active": True, "company_name": "Tech Corp"},
        {"_id": ObjectId("660000000000000000000011"), "name": "HR Two", "email": "hr2@test.com", "role": "hr", "is_active": True, "company_name": "Biz Inc"},
        {"_id": ObjectId("660000000000000000000012"), "name": "Seeker One", "email": "s1@test.com", "role": "seeker", "is_active": True},
    ])

def test_hr_create_job_flow(client, hr1_token, mock_db):
    # Construct a detailed job description that triggers parsing
    jd_description = (
        "We are looking for a senior Python software engineer.\n"
        "Must Have Skills:\n"
        "Python, FastAPI, MongoDB, SQL\n"
        "Nice to Have:\n"
        "Docker, AWS, React, machine learning\n"
        "We require at least 5 years of experience.\n"
        "Education required: Master's degree in Computer Science.\n"
        "This is a full-time, remote position."
    )

    headers = {"Authorization": f"Bearer {hr1_token}"}
    payload = {
        "title": "Senior Python Engineer",
        "description": jd_description,
        "required_skills": ["git"], # manually added
        "experience_required": None,
        "location": None,
        "salary_min": 60000,
        "salary_max": 90000,
        "is_template": False,
        "status": "open"
    }

    response = client.post("/api/hr/jobs", json=payload, headers=headers)
    assert response.status_code == 201
    job_data = response.json()
    job_id = job_data["id"]
    
    assert job_data["title"] == "Senior Python Engineer"
    assert job_data["company_name"] == "Tech Corp"
    assert job_data["status"] == "open"
    
    # Skills check (normalized casing and merged with manual entry)
    assert "python" in job_data["required_skills"]
    assert "git" in job_data["required_skills"]
    assert "fastapi" in job_data["required_skills"]
    assert "docker" in job_data["preferred_skills"]
    assert "aws" in job_data["preferred_skills"]
    
    # Auto-extracted values
    assert job_data["experience_required"] == 5.0
    assert job_data["education_required"] == "Master's"
    assert job_data["employment_type"] == "Full-time"
    assert job_data["location"] == "Remote"
    assert job_data["salary_range"]["min"] == 60000
    assert job_data["salary_range"]["max"] == 90000

    # 2. Get Job details
    response_get = client.get(f"/api/hr/jobs/{job_id}", headers=headers)
    assert response_get.status_code == 200
    assert response_get.json()["title"] == "Senior Python Engineer"

    # 3. Update Job details
    update_payload = {
        "title": "Senior Python/FastAPI Engineer",
        "status": "draft"
    }
    response_put = client.put(f"/api/hr/jobs/{job_id}", json=update_payload, headers=headers)
    assert response_put.status_code == 200
    assert response_put.json()["title"] == "Senior Python/FastAPI Engineer"
    assert response_put.json()["status"] == "draft"

    # 4. Duplicate Job
    response_dup = client.post(f"/api/hr/jobs/{job_id}/duplicate", headers=headers)
    assert response_dup.status_code == 200
    dup_data = response_dup.json()
    assert dup_data["title"] == "Copy of Senior Python/FastAPI Engineer"
    assert dup_data["id"] != job_id

    # 5. Delete Job
    response_del = client.delete(f"/api/hr/jobs/{job_id}", headers=headers)
    assert response_del.status_code == 200
    assert mock_db.sync_db["job_posts"].find_one({"_id": ObjectId(job_id)}) is None

def test_job_security_and_role_permissions(client, hr1_token, hr2_token, seeker_token, mock_db):
    # Insert a job post belonging to HR One
    job_doc = {
        "hr_id": ObjectId("660000000000000000000010"),
        "title": "React Developer",
        "description_text": "Sample description of a job post that must be at least fifty characters long for validation rules.",
        "required_skills": ["react"],
        "status": "open",
        "is_template": False
    }
    result = mock_db.sync_db["job_posts"].insert_one(job_doc)
    job_id = str(result.inserted_id)

    # A Seeker attempts to create a job (Forbidden)
    seeker_headers = {"Authorization": f"Bearer {seeker_token}"}
    response_seeker = client.post("/api/hr/jobs", json={"title": "Test", "description": "Short"}, headers=seeker_headers)
    assert response_seeker.status_code == 403

    # HR Two attempts to update HR One's job (Forbidden)
    hr2_headers = {"Authorization": f"Bearer {hr2_token}"}
    response_hr2 = client.put(f"/api/hr/jobs/{job_id}", json={"title": "Malicious Update"}, headers=hr2_headers)
    assert response_hr2.status_code == 403

    # HR Two attempts to delete HR One's job (Forbidden)
    response_del = client.delete(f"/api/hr/jobs/{job_id}", headers=hr2_headers)
    assert response_del.status_code == 403

def test_job_validation_rules(client, hr1_token):
    headers = {"Authorization": f"Bearer {hr1_token}"}
    
    # Title too short
    payload = {
        "title": "Hi",
        "description": "This is a descriptive description that should pass length validations because it is long enough."
    }
    assert client.post("/api/hr/jobs", json=payload, headers=headers).status_code == 400

    # Description too short
    payload2 = {
        "title": "Software Developer",
        "description": "Too short description"
    }
    assert client.post("/api/hr/jobs", json=payload2, headers=headers).status_code == 400

    # Negative experience
    payload3 = {
        "title": "Software Developer",
        "description": "This is a descriptive description that should pass length validations because it is long enough.",
        "experience_required": -1
    }
    assert client.post("/api/hr/jobs", json=payload3, headers=headers).status_code == 400

    # Invalid status
    payload4 = {
        "title": "Software Developer",
        "description": "This is a descriptive description that should pass length validations because it is long enough.",
        "status": "invalid_status"
    }
    assert client.post("/api/hr/jobs", json=payload4, headers=headers).status_code == 400

    # Min salary negative
    payload5 = {
        "title": "Software Developer",
        "description": "This is a descriptive description that should pass length validations because it is long enough.",
        "salary_min": -100
    }
    assert client.post("/api/hr/jobs", json=payload5, headers=headers).status_code == 400

    # Max salary less than min salary
    payload6 = {
        "title": "Software Developer",
        "description": "This is a descriptive description that should pass length validations because it is long enough.",
        "salary_min": 5000,
        "salary_max": 4000
    }
    assert client.post("/api/hr/jobs", json=payload6, headers=headers).status_code == 400
