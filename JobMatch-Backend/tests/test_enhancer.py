import pytest
from bson import ObjectId
from app.core.security import create_access_token
from app.services.resume_enhancer import resume_enhancer_service

@pytest.fixture
def seeker1_token():
    return create_access_token({"sub": "660000000000000000000022", "role": "seeker"})

@pytest.fixture
def seeker2_token():
    return create_access_token({"sub": "660000000000000000000023", "role": "seeker"})

@pytest.fixture(autouse=True)
def setup_data(mock_db):
    mock_db.sync_db["users"].insert_many([
        {"_id": ObjectId("660000000000000000000022"), "name": "Seeker One", "role": "seeker", "is_active": True},
        {"_id": ObjectId("660000000000000000000023"), "name": "Seeker Two", "role": "seeker", "is_active": True},
    ])
    mock_db.sync_db["resumes"].insert_many([
        {
            "_id": ObjectId("660000000000000000000050"),
            "user_id": ObjectId("660000000000000000000022"), # Seeker One owns it
            "extracted_text": "Alice Jenkins\nEmail: alice@test.com\nPhone: +1-444-555-6666\n\nProfessional Summary\nSoftware Developer.\n\nWork Experience\nWorked as a software engineer. 5 years of experience.\n\nEducation\nMaster of Science in Computer Science.\n\nSkills\nPython, FastAPI, MongoDB, Git.\n\nProjects\nBuilt a match engine.",
            "file_type": ".pdf"
        },
        {
            "_id": ObjectId("660000000000000000000051"),
            "user_id": ObjectId("660000000000000000000023"), # Seeker Two owns it
            "extracted_text": "Short text.",
            "file_type": ".txt"
        }
    ])
    mock_db.sync_db["job_posts"].insert_many([
        {
            "_id": ObjectId("660000000000000000000060"),
            "title": "Backend Engineer",
            "company_name": "Acme Corp",
            "description_text": "We need a Backend Developer. Must know Python, FastAPI, and Docker. Master's degree preferred.",
            "required_skills": ["python", "fastapi", "docker"],
            "preferred_skills": ["kubernetes", "mongodb"],
            "experience_required": 3.0,
            "education_required": "Master's",
            "status": "open"
        }
    ])

def test_resume_enhancer_analysis_logic():
    # Successful enhancement
    res = resume_enhancer_service.analyze(
        resume_text="Alice Jenkins\nEmail: alice@test.com\nPhone: +1-444-555-6666\n\nProfessional Summary\nSoftware Developer.\n\nWork Experience\nWorked as a software engineer. 5 years of experience.\n\nEducation\nMaster of Science in Computer Science.\n\nSkills\nPython, FastAPI, MongoDB, Git.\n\nProjects\nBuilt a match engine.",
        jd_text="We need a Backend Developer. Must know Python, FastAPI, and Docker.",
        required_skills=["python", "fastapi", "docker"],
        preferred_skills=["kubernetes", "mongodb"],
        exp_required=3.0,
        edu_required="Master's"
    )

    assert res["overall_score"] > 40
    assert res["score"] == res["overall_score"]

    # Required/Preferred skill separation
    assert "python" in res["matched_required_skills"]
    assert "fastapi" in res["matched_required_skills"]
    assert "docker" in res["missing_required_skills"]
    assert "mongodb" in res["matched_preferred_skills"]
    assert "kubernetes" in res["missing_preferred_skills"]

    # Important keyword gaps
    assert "docker" in res["important_missing_keywords"]

    # Section analysis
    assert "Work Experience" in res["detected_sections"]
    assert "Certifications" in res["missing_recommended_sections"]

    # Experience/Education comparison
    assert res["experience"]["candidate"] == 5.0
    assert res["experience"]["required"] == 3.0
    assert res["experience"]["status"] == "meets_requirement"
    
    assert res["education"]["candidate"] == "Master's"
    assert res["education"]["required"] == "Master's"
    assert res["education"]["match"] is True

    # Actionable suggestions and priority
    high_suggestions = [s for s in res["prioritized_actionable_improvements"] if s["priority"] == "High"]
    assert any("docker" in s["text"].lower() for s in high_suggestions)

def test_enhancer_empty_text():
    res = resume_enhancer_service.analyze("", "Some job description.")
    assert "error" in res

def test_secure_resume_enhancer_endpoint(client, seeker1_token, seeker2_token):
    headers1 = {"Authorization": f"Bearer {seeker1_token}"}
    headers2 = {"Authorization": f"Bearer {seeker2_token}"}

    # 1. Seeker 1 enhances their own resume (Authorized)
    payload = {
        "resume_id": "660000000000000000000050",
        "job_id": "660000000000000000000060"
    }
    response = client.post("/api/seeker/resume-enhancer", json=payload, headers=headers1)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["overall_score"] > 40

    # 2. Seeker 2 enhances Seeker 1's resume (Forbidden)
    response = client.post("/api/seeker/resume-enhancer", json=payload, headers=headers2)
    assert response.status_code == 403

    # 3. Direct JD text input (No job_id)
    payload_direct = {
        "resume_id": "660000000000000000000050",
        "jd_text": "We need Python and FastAPI backend development."
    }
    response = client.post("/api/seeker/resume-enhancer", json=payload_direct, headers=headers1)
    assert response.status_code == 200
    assert response.json()["overall_score"] > 30

    # 4. Invalid resume ID / Job ID
    response = client.post("/api/seeker/resume-enhancer", json={"resume_id": "660000000000000000000088", "job_id": "660000000000000000000060"}, headers=headers1)
    assert response.status_code == 404
