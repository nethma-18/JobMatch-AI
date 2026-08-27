import pytest
from bson import ObjectId
from unittest.mock import patch, MagicMock
from app.core.security import create_access_token
from app.ml.similarity import similarity_engine
from app.services.job_ranking import job_ranking_service
from app.services.blind_screener import blind_screener_service

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
        {"_id": ObjectId("660000000000000000000020"), "name": "HR One", "email": "hr1@test.com", "role": "hr", "is_active": True},
        {"_id": ObjectId("660000000000000000000021"), "name": "HR Two", "email": "hr2@test.com", "role": "hr", "is_active": True},
        {"_id": ObjectId("660000000000000000000022"), "name": "Seeker One", "email": "s1@test.com", "role": "seeker", "is_active": True},
    ])
    mock_db.sync_db["job_posts"].insert_many([
        {
            "_id": ObjectId("660000000000000000000030"),
            "hr_id": ObjectId("660000000000000000000020"),
            "title": "React Developer",
            "description_text": "Sample job description seeking React, JavaScript, and HTML.",
            "required_skills": ["react", "javascript"],
            "preferred_skills": ["docker", "typescript"],
            "status": "open"
        }
    ])
    mock_db.sync_db["resumes"].insert_many([
        {
            "_id": ObjectId("660000000000000000000040"),
            "user_id": ObjectId("660000000000000000000022"),
            "extracted_text": "I am a frontend developer with experience in React and JavaScript.",
            "original_filename": "resume1.pdf"
        },
        {
            "_id": ObjectId("660000000000000000000041"),
            "user_id": ObjectId("660000000000000000000022"),
            "extracted_text": "Full stack engineer. Proficient in React, JavaScript, Docker, and TypeScript.",
            "original_filename": "resume2.pdf"
        }
    ])
    mock_db.sync_db["ranking_queue"].insert_many([
        {
            "job_id": ObjectId("660000000000000000000030"),
            "resume_id": ObjectId("660000000000000000000040"),
            "candidate_name": "John Doe"
        },
        {
            "job_id": ObjectId("660000000000000000000030"),
            "resume_id": ObjectId("660000000000000000000041"),
            "candidate_name": "Jane Smith"
        }
    ])

def test_similarity_calculation():
    # 1. Identical text produces high score
    text = "We need React, JavaScript, and Docker experience."
    res = similarity_engine.compute_match(
        resume_text=text,
        jd_text=text,
        required_skills=["react", "javascript"],
        preferred_skills=["docker"]
    )
    assert res["match_score"] > 80
    assert "react" in res["matched_required_skills"]
    assert "docker" in res["matched_preferred_skills"]
    assert res["interview_eligible"] is True

    # 2. Empty input handling
    res_empty = similarity_engine.compute_match("", "Some Job Description")
    assert res_empty["score"] == 0

    # 3. No required skills does not divide by zero
    res_no_req = similarity_engine.compute_match(
        resume_text="I know everything",
        jd_text="General position",
        required_skills=[],
        preferred_skills=[]
    )
    assert res_no_req["match_score"] >= 0
    assert res_no_req["required_skill_overlap_available"] is False

@patch("app.ml.embeddings.embedding_engine.is_ready")
def test_tfidf_fallback_activation(mock_is_ready):
    # Force embedding engine to report not ready to trigger tfidf fallback
    mock_is_ready.return_value = False
    res = similarity_engine.compute_match(
        resume_text="React developer",
        jd_text="React position",
        required_skills=["react"],
        preferred_skills=[]
    )
    assert res["similarity_method"] == "tfidf_fallback"
    assert res["match_score"] > 0

def test_ranking_sorting_and_determinism():
    resumes = [
        {"id": "c1", "text": "I know python", "filename": "c1.pdf", "candidate_name": "Alice"},
        {"id": "c2", "text": "I know python and fastapi", "filename": "c2.pdf", "candidate_name": "Bob"},
        {"id": "c3", "text": "I know python", "filename": "c3.pdf", "candidate_name": "Charlie"},
    ]
    # Alice and Charlie have identical text (same score)
    # Bob has better text (higher score)
    ranked = similarity_engine.rank_resumes(
        jd_text="Python developer with fastapi",
        resumes=resumes,
        required_skills=["python", "fastapi"],
        top_n=5
    )
    assert ranked[0]["candidate_id"] == "c2" # Highest score first
    
    # Alice and Charlie should sort deterministically by their candidate_id string value
    # str("c1") < str("c3"), so Alice should be rank 2 and Charlie rank 3
    assert ranked[1]["candidate_id"] == "c1"
    assert ranked[2]["candidate_id"] == "c3"

def test_blind_screening_anonymization():
    item = {
        "candidate_id": "123",
        "candidate_name": "Alice Jenkins",
        "filename": "alice_resume.pdf",
        "email": "alice@gmail.com",
        "phone": "+1-234-567-8900",
        "location": "New York",
        "text": "Call me at +1-234-567-8900 or email alice@gmail.com. I worked at Stanford."
    }
    anonymized = blind_screener_service.anonymize_candidate(item, index=1)
    
    assert anonymized["candidate_name"] == "Candidate #1"
    assert anonymized["filename"] == "Resume_Candidate_1.pdf"
    assert anonymized["email"] == "[ANONYMIZED]"
    assert anonymized["phone"] == "[ANONYMIZED]"
    assert anonymized["location"] == "[ANONYMIZED]"
    assert "[ANONYMIZED EMAIL]" in anonymized["text"]
    assert "[ANONYMIZED PHONE]" in anonymized["text"]
    assert "Stanford" in anonymized["text"] # direct non-PII words remain

def test_secure_ranking_api_endpoints(client, hr1_token, hr2_token, seeker_token):
    # HR One ranks their own job (Authorized)
    headers1 = {"Authorization": f"Bearer {hr1_token}"}
    response1 = client.post("/api/hr/job-ranking/660000000000000000000030", headers=headers1)
    assert response1.status_code == 200
    assert len(response1.json()["rankings"]) == 2

    # Seeker attempts to rank job (Forbidden)
    seeker_headers = {"Authorization": f"Bearer {seeker_token}"}
    response_seeker = client.post("/api/hr/job-ranking/660000000000000000000030", headers=seeker_headers)
    assert response_seeker.status_code == 403

    # HR Two attempts to rank HR One's job (Forbidden)
    headers2 = {"Authorization": f"Bearer {hr2_token}"}
    response_hr2 = client.post("/api/hr/job-ranking/660000000000000000000030", headers=headers2)
    assert response_hr2.status_code == 403

    # HR Two attempts to get HR One's job rankings (Forbidden)
    response_get = client.get("/api/hr/rankings/660000000000000000000030", headers=headers2)
    assert response_get.status_code == 403
