import pytest
from bson import ObjectId
from app.core.security import create_access_token
from app.services.ats_checker import ats_checker_service

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
            "_id": ObjectId("660000000000000000000040"),
            "user_id": ObjectId("660000000000000000000022"), # Seeker One owns it
            "extracted_text": "John Doe\nEmail: john@test.com\nPhone: +1-234-567-8900\n\nProfessional Summary\nAn experienced developer.\n\nWork Experience\nWorked at Google for 5 years.\n\nEducation\nBachelor of Science in Computer Science.\n\nSkills\nPython, FastAPI, MongoDB, Docker, Git.\n\nProjects\nBuilt a resume parser.",
            "file_type": ".pdf"
        },
        {
            "_id": ObjectId("660000000000000000000041"),
            "user_id": ObjectId("660000000000000000000023"), # Seeker Two owns it
            "extracted_text": "Brief text.",
            "file_type": ".txt"
        }
    ])

def test_ats_checker_scoring_and_features():
    # 1. Strong resume receives appropriate score and validates details
    res = ats_checker_service.check(
        resume_text="John Doe\nEmail: john@test.com\nPhone: +1-234-567-8900\n\nProfessional Summary\nDeveloper.\n\nWork Experience\nGoogle.\n\nEducation\nBSc.\n\nSkills\nPython, FastAPI, MongoDB, Docker.",
        file_extension=".pdf",
        jd_text="Need python, fastapi, and mongodb."
    )
    
    assert res["ats_score"] > 60
    assert res["score"] == res["ats_score"]
    assert sum(res["breakdown"].values()) == res["score"] # sum equals final score
    assert res["contact"]["has_name"] is True
    assert res["contact"]["has_email"] is True
    assert res["contact"]["has_phone"] is True
    
    # Assert private values are NOT returned
    assert "john@test.com" not in str(res["contact"])
    assert "+1-234-567-8900" not in str(res["contact"])

    # Grade is valid
    assert res["grade"] in ["Excellent", "Very Good", "Good", "Fair", "Needs Improvement"]

    # Keyword alignment works with JD
    assert "python" in res["skills"]["matched_required"]
    assert "mongodb" in res["skills"]["matched_required"]
    
    # 2. Section detection
    assert "Work Experience" in res["sections_found"]
    assert "Education" in res["sections_found"]
    assert "Skills" in res["sections_found"]

    # 3. Weak resume receives lower score
    res_weak = ats_checker_service.check(
        resume_text="Brief resume without headings.",
        file_extension=".txt"
    )
    assert res_weak["ats_score"] < 60

    # 4. Technical symbols are not penalized
    res_tech = ats_checker_service.check(
        resume_text="John Doe\njohn@test.com\n1234567\n\nWork Experience\nCoding in C++ and C# and .NET and Node.js. Querying SQL. We designed robust scalable microservices and databases. We achieved a highly structured data parsing methodology. We deployed cloud native applications to AWS EC2 and used Docker containers. Additionally, we maintained legacy frameworks in PHP and integrated modern CI/CD pipelines using GitHub Actions. We also worked on Kubernetes orchestrations for distributed data processing engines and optimized indexing strategies for relational databases.",
        file_extension=".pdf"
    )
    assert res_tech["breakdown"]["text_extractability"] >= 15 # not flagged as gibberish

def test_ats_checker_empty_and_no_jd():
    # Empty resume
    res_empty = ats_checker_service.check("")
    assert res_empty["ats_score"] == 0

    # Resume without JD
    res_no_jd = ats_checker_service.check(
        resume_text="John Doe\nEmail: john@test.com\nPhone: +1-234-567-8900\n\nWork Experience\nDeveloped systems.\n\nEducation\nBSc CS.\n\nSkills\nPython, Java.",
        file_extension=".docx"
    )
    assert res_no_jd["ats_score"] > 50
    assert "Upload a job description" in res_no_jd["improvements"][-1]

def test_secure_ats_checker_endpoint(client, seeker1_token, seeker2_token):
    headers1 = {"Authorization": f"Bearer {seeker1_token}"}
    headers2 = {"Authorization": f"Bearer {seeker2_token}"}

    # Seeker 1 checks their own resume (Authorized)
    payload = {"resume_id": "660000000000000000000040"}
    response = client.post("/api/seeker/ats-checker", json=payload, headers=headers1)
    assert response.status_code == 200

    # Seeker 2 checks Seeker 1's resume (Forbidden)
    response = client.post("/api/seeker/ats-checker", json=payload, headers=headers2)
    assert response.status_code == 403
