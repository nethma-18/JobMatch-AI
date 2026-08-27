import pytest
from bson import ObjectId
from app.core.security import create_access_token
from app.services.cover_letter import cover_letter_service

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
        }
    ])
    mock_db.sync_db["job_posts"].insert_many([
        {
            "_id": ObjectId("660000000000000000000060"),
            "title": "Backend Engineer",
            "company_name": "Acme Corp",
            "description_text": "We need a Backend Developer. Must know Python, FastAPI, and Docker.",
            "required_skills": ["python", "fastapi", "docker"],
            "preferred_skills": ["kubernetes", "mongodb"],
            "experience_required": 3.0,
            "education_required": "Master's",
            "status": "open"
        }
    ])

def test_cover_letter_generation_tones():
    resume_text = "Alice Jenkins\nWorked as a software engineer. 5 years of experience.\nMaster of Science.\nSkills: Python, FastAPI."
    jd_text = "Backend Developer role. Requires Python, FastAPI, Docker."

    # 1. Professional Tone
    res_prof = cover_letter_service.generate(
        resume_text=resume_text,
        jd_text=jd_text,
        tone="professional"
    )
    assert "strong interest" in res_prof["cover_letter"]
    assert "5 years" in res_prof["cover_letter"]
    assert "python" in res_prof["matched_skills_used"]

    # 2. Enthusiastic Tone
    res_enth = cover_letter_service.generate(
        resume_text=resume_text,
        jd_text=jd_text,
        tone="enthusiastic"
    )
    assert "thrilled" in res_enth["cover_letter"] or "excited" in res_enth["cover_letter"]

    # 3. Concise Tone
    res_conc = cover_letter_service.generate(
        resume_text=resume_text,
        jd_text=jd_text,
        tone="concise"
    )
    assert "Please accept this application" in res_conc["cover_letter"]
    
    # 4. Empty validation
    res_empty = cover_letter_service.generate("", "")
    assert "error" in res_empty

def test_unsupported_qualifications_prevention():
    resume_text = "Alice Jenkins\nSkills: Python, Git."
    jd_text = "We need a PhD Backend Engineer who has Google experience and worked with Docker."

    res = cover_letter_service.generate(
        resume_text=resume_text,
        jd_text=jd_text,
        required_skills=["docker"],
        edu_required="PhD"
    )

    # Assert it DOES NOT invent PhD, Google or Docker since they aren't on the resume!
    assert "google" not in res["cover_letter"].lower()
    assert "phd" not in res["cover_letter"].lower()
    assert "docker" not in res["cover_letter"].lower()
    assert "python" in res["cover_letter"].lower() # supported!

def test_secure_cover_letter_endpoints(client, seeker1_token, seeker2_token):
    headers1 = {"Authorization": f"Bearer {seeker1_token}"}
    headers2 = {"Authorization": f"Bearer {seeker2_token}"}

    payload = {
        "resume_id": "660000000000000000000050",
        "job_id": "660000000000000000000060",
        "tone": "professional"
    }

    # 1. Seeker 1 generates cover letter using own resume (Authorized)
    response = client.post("/api/seeker/cover-letter", json=payload, headers=headers1)
    assert response.status_code == 200
    res_data = response.json()
    assert "cover_letter_id" in res_data
    letter_id = res_data["cover_letter_id"]

    # 2. Seeker 2 generates using Seeker 1's resume (Forbidden)
    response = client.post("/api/seeker/cover-letter", json=payload, headers=headers2)
    assert response.status_code == 403

    # 3. Direct JD text input (No job_id)
    payload_direct = {
        "resume_id": "660000000000000000000050",
        "jd_text": "We need Python and FastAPI backend development.",
        "tone": "concise"
    }
    response = client.post("/api/seeker/cover-letter", json=payload_direct, headers=headers1)
    assert response.status_code == 200

    # 4. Save and Update letter edits (PUT)
    response = client.put(f"/api/seeker/cover-letter/{letter_id}", json={"edited_text": "Edited Cover Letter"}, headers=headers1)
    assert response.status_code == 200
    assert response.json()["message"] == "Cover letter saved"
