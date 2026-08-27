import pytest
from bson import ObjectId
from app.core.security import create_access_token

@pytest.fixture
def hr1_token():
    return create_access_token({"sub": "660000000000000000000020", "role": "hr"})

@pytest.fixture
def hr2_token():
    return create_access_token({"sub": "660000000000000000000021", "role": "hr"})

@pytest.fixture
def seeker_token():
    return create_access_token({"sub": "660000000000000000000022", "role": "seeker"})

@pytest.fixture(autouse=True)
def setup_data(mock_db):
    mock_db.sync_db["users"].insert_many([
        {"_id": ObjectId("660000000000000000000020"), "name": "HR One", "role": "hr", "is_active": True},
        {"_id": ObjectId("660000000000000000000021"), "name": "HR Two", "role": "hr", "is_active": True},
        {"_id": ObjectId("660000000000000000000022"), "name": "Seeker One", "role": "seeker", "is_active": True},
    ])
    mock_db.sync_db["job_posts"].insert_many([
        {
            "_id": ObjectId("660000000000000000000030"),
            "hr_id": ObjectId("660000000000000000000020"),
            "title": "Python Dev",
            "description_text": "Need python, fastapi, and mongodb.",
            "required_skills": ["python", "fastapi", "mongodb"],
            "preferred_skills": ["docker"],
            "experience_required": 3.0,
            "education_required": "Bachelor's",
            "status": "open"
        },
        {
            "_id": ObjectId("660000000000000000000031"),
            "hr_id": ObjectId("660000000000000000000020"),
            "title": "No Req Dev",
            "description_text": "General role.",
            "required_skills": [],
            "preferred_skills": [],
            "experience_required": 0,
            "education_required": None,
            "status": "open"
        }
    ])
    mock_db.sync_db["resumes"].insert_many([
        {
            "_id": ObjectId("660000000000000000000040"),
            "user_id": ObjectId("660000000000000000000020"), # Uploaded by HR One directly
            "extracted_text": "I know python, fastapi, and mongodb. I have 5 years experience and a phd degree.",
            "original_filename": "res1.pdf",
            "candidate_name": "Alice Jenkins"
        },
        {
            "_id": ObjectId("660000000000000000000041"),
            "user_id": ObjectId("660000000000000000000022"), # Uploaded by Seeker One
            "extracted_text": "I know python, docker, and react. Unknown education.",
            "original_filename": "res2.pdf",
            "candidate_name": "Bob Smith"
        }
    ])
    # Link resume2 to job30 (so HR One is authorized to analyze it)
    mock_db.sync_db["ranking_queue"].insert_one({
        "job_id": ObjectId("660000000000000000000030"),
        "resume_id": ObjectId("660000000000000000000041"),
        "candidate_name": "Bob Smith"
    })

def test_skill_gap_success_cases(client, hr1_token):
    headers = {"Authorization": f"Bearer {hr1_token}"}
    
    # Candidate 1: matches all required (python, fastapi, mongodb), preferred docker is missing, extra skill phd
    payload = {
        "resume_id": "660000000000000000000040",
        "job_id": "660000000000000000000030"
    }
    response = client.post("/api/hr/skill-gap", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert data["match_percentage"] == 100.0
    assert len(data["matched_skills"]) == 3
    assert len(data["missing_skills"]) == 0
    assert "docker" in data["preferred_skills"]["missing"]
    assert data["gap_severity"] == "None"
    assert data["experience"]["candidate"] == 5.0
    assert data["experience"]["status"] == "meets_requirement"
    assert data["education"]["candidate"] == "PhD"
    assert data["education"]["match"] is True

    # Candidate 2: partial matches
    payload2 = {
        "resume_id": "660000000000000000000041",
        "job_id": "660000000000000000000030"
    }
    response2 = client.post("/api/hr/skill-gap", json=payload2, headers=headers)
    assert response2.status_code == 200
    data2 = response2.json()
    # matches: python (1 of 3 required) -> 33.3% coverage
    assert data2["match_percentage"] == 33.3
    # missing required: fastapi, mongodb (2 of 3 missing -> 66.6% missing -> Critical severity)
    assert data2["gap_severity"] == "Critical"
    assert "docker" in data2["preferred_skills"]["matched"] # matched preferred skill!
    assert "react" in data2["extra_skills"] # extra candidate skill!
    # Experience not mentioned in Bob's resume
    assert data2["experience"]["candidate"] is None
    assert data2["experience"]["status"] == "unknown"
    # Education unknown
    assert data2["education"]["candidate"] is None
    assert data2["education"]["match"] == "unknown"

def test_skill_gap_severity_levels(client, hr1_token, mock_db):
    headers = {"Authorization": f"Bearer {hr1_token}"}
    
    # Insert new job with 5 skills
    mock_db.sync_db["job_posts"].insert_one({
        "_id": ObjectId("660000000000000000000035"),
        "hr_id": ObjectId("660000000000000000000020"),
        "title": "5-Skill Job",
        "description_text": "Need python, fastapi, mongodb, docker, aws.",
        "required_skills": ["python", "fastapi", "mongodb", "docker", "aws"],
        "status": "open"
    })
    
    # Resume with 4 out of 5 skills (1 missing -> 20% missing -> Low gap severity)
    mock_db.sync_db["resumes"].insert_one({
        "_id": ObjectId("660000000000000000000045"),
        "user_id": ObjectId("660000000000000000000020"),
        "extracted_text": "I know python, fastapi, mongodb, and docker.",
    })
    
    payload = {
        "resume_id": "660000000000000000000045",
        "job_id": "660000000000000000000035"
    }
    response = client.post("/api/hr/skill-gap", json=payload, headers=headers)
    assert response.json()["gap_severity"] == "Low"

    # Resume with 3 out of 5 skills (2 missing -> 40% missing -> Medium gap severity)
    mock_db.sync_db["resumes"].insert_one({
        "_id": ObjectId("660000000000000000000046"),
        "user_id": ObjectId("660000000000000000000020"),
        "extracted_text": "I know python, fastapi, and mongodb.",
    })
    payload["resume_id"] = "660000000000000000000046"
    response = client.post("/api/hr/skill-gap", json=payload, headers=headers)
    assert response.json()["gap_severity"] == "Medium"

    # Resume with 2 out of 5 skills (3 missing -> 60% missing -> High gap severity)
    mock_db.sync_db["resumes"].insert_one({
        "_id": ObjectId("660000000000000000000047"),
        "user_id": ObjectId("660000000000000000000020"),
        "extracted_text": "I know python and fastapi.",
    })
    payload["resume_id"] = "660000000000000000000047"
    response = client.post("/api/hr/skill-gap", json=payload, headers=headers)
    assert response.json()["gap_severity"] == "High"

def test_zero_required_skills(client, hr1_token):
    headers = {"Authorization": f"Bearer {hr1_token}"}
    payload = {
        "resume_id": "660000000000000000000040",
        "job_id": "660000000000000000000031"
    }
    response = client.post("/api/hr/skill-gap", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["gap_severity"] == "Not Applicable"
    assert data["match_percentage"] == 100.0

def test_blind_screening_skill_gap(client, hr1_token):
    headers = {"Authorization": f"Bearer {hr1_token}"}
    payload = {
        "resume_id": "660000000000000000000040",
        "job_id": "660000000000000000000030",
        "blind_mode": True
    }
    response = client.post("/api/hr/skill-gap", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["candidate_name"] == "Candidate"
    assert data["filename"] == "Resume_Candidate.pdf"

def test_security_rules(client, hr1_token, hr2_token, seeker_token):
    # Seeker gets blocked (403)
    payload = {
        "resume_id": "660000000000000000000040",
        "job_id": "660000000000000000000030"
    }
    response = client.post("/api/hr/skill-gap", json=payload, headers={"Authorization": f"Bearer {seeker_token}"})
    assert response.status_code == 403

    # HR Two cannot analyze HR One's resume directly (403)
    response = client.post("/api/hr/skill-gap", json=payload, headers={"Authorization": f"Bearer {hr2_token}"})
    assert response.status_code == 403

    # Job Not Found (404)
    payload_bad_job = {
        "resume_id": "660000000000000000000040",
        "job_id": "660000000000000000000099"
    }
    response = client.post("/api/hr/skill-gap", json=payload_bad_job, headers={"Authorization": f"Bearer {hr1_token}"})
    assert response.status_code == 404
