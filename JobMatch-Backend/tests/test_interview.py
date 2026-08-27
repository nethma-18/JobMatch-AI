import pytest
from bson import ObjectId
from app.core.security import create_access_token
from app.services.interview_questions import interview_questions_service

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

def test_question_count_limits_and_categories():
    resume_text = "Alice Jenkins\nWorked as a software engineer. 5 years of experience.\nSkills: Python, FastAPI, MongoDB."
    jd_text = "Backend Developer position. Required: Python, Docker."

    # 1. 5-question generation
    res_5 = interview_questions_service.generate(
        resume_text=resume_text,
        jd_text=jd_text,
        num_questions=5,
        required_skills=["python", "docker"]
    )
    assert res_5["total"] == 5
    assert len(res_5["questions"]) == 5

    # 2. 20-question generation
    res_20 = interview_questions_service.generate(
        resume_text=resume_text,
        jd_text=jd_text,
        num_questions=20,
        required_skills=["python", "docker"]
    )
    assert res_20["total"] <= 20
    assert len(res_20["questions"]) > 0

    # 3. Invalid question count (< 5)
    res_invalid_low = interview_questions_service.generate(resume_text, jd_text, num_questions=2)
    assert "error" in res_invalid_low

    # 4. Invalid question count (> 20)
    res_invalid_high = interview_questions_service.generate(resume_text, jd_text, num_questions=25)
    assert "error" in res_invalid_high

    # 5. Category & Difficulty classification
    cats = {q["category"] for q in res_5["questions"]}
    diffs = {q["difficulty"] for q in res_5["questions"]}
    assert len(cats) > 0
    assert diffs.issubset({"Easy", "Medium", "Hard"})

    # Check why_relevant and related_skill present
    for q in res_5["questions"]:
        assert "why_relevant" in q
        assert "related_skill" in q

def test_prevention_of_invented_candidate_info():
    resume_text = "Alice Jenkins\nSkills: Python, Git."
    jd_text = "We need a PhD Backend Engineer who has Google experience and worked with Docker."

    res = interview_questions_service.generate(
        resume_text=resume_text,
        jd_text=jd_text,
        required_skills=["docker"],
        num_questions=6
    )

    # Convert all questions to lowercase string
    all_q_text = " ".join([q["question"].lower() + " " + q["why_relevant"].lower() for q in res["questions"]])

    # Assert no invented Google / PhD claims about candidate
    assert "phd" not in all_q_text
    assert "google" not in all_q_text

def test_secure_interview_questions_endpoints(client, seeker1_token, seeker2_token):
    headers1 = {"Authorization": f"Bearer {seeker1_token}"}
    headers2 = {"Authorization": f"Bearer {seeker2_token}"}

    payload = {
        "resume_id": "660000000000000000000050",
        "job_id": "660000000000000000000060",
        "num_questions": 8
    }

    # 1. Seeker 1 generates questions (Authorized)
    response = client.post("/api/seeker/interview-questions", json=payload, headers=headers1)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["total"] == 8

    # 2. Seeker 2 generates using Seeker 1's resume (Forbidden)
    response = client.post("/api/seeker/interview-questions", json=payload, headers=headers2)
    assert response.status_code == 403

    # 3. Invalid question count rejected by router
    payload_invalid = {
        "resume_id": "660000000000000000000050",
        "job_id": "660000000000000000000060",
        "num_questions": 30
    }
    response = client.post("/api/seeker/interview-questions", json=payload_invalid, headers=headers1)
    assert response.status_code == 400

    # 4. Direct JD text
    payload_direct = {
        "resume_id": "660000000000000000000050",
        "jd_text": "Need Python and FastAPI.",
        "num_questions": 6
    }
    response = client.post("/api/seeker/interview-questions", json=payload_direct, headers=headers1)
    assert response.status_code == 200
