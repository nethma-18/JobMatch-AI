import pytest
from bson import ObjectId
from unittest.mock import patch, AsyncMock
from app.core.security import create_access_token
from app.validation.pipeline import validation_pipeline

# A dummy resume PDF file content
DUMMY_PDF_CONTENT = b"%PDF-1.4 ... dummy content ..."

@pytest.fixture
def seeker1_token():
    return create_access_token({"sub": "660000000000000000000001", "role": "seeker"})

@pytest.fixture
def seeker2_token():
    return create_access_token({"sub": "660000000000000000000002", "role": "seeker"})

@pytest.fixture
def hr_token():
    return create_access_token({"sub": "660000000000000000000003", "role": "hr"})

@pytest.fixture(autouse=True)
def setup_users(mock_db):
    # Setup mock users in DB
    mock_db.sync_db["users"].insert_many([
        {"_id": ObjectId("660000000000000000000001"), "name": "Seeker One", "email": "s1@test.com", "role": "seeker", "is_active": True},
        {"_id": ObjectId("660000000000000000000002"), "name": "Seeker Two", "email": "s2@test.com", "role": "seeker", "is_active": True},
        {"_id": ObjectId("660000000000000000000003"), "name": "HR One", "email": "hr1@test.com", "role": "hr", "is_active": True, "company_name": "Test Co"},
    ])

@patch("app.utils.file_utils.save_upload")
@patch("app.ml.text_extractor.text_extractor.extract")
@patch("app.validation.pipeline.validation_pipeline.run")
def test_upload_resume_flow(mock_validation_run, mock_extract, mock_save_upload, client, seeker1_token, seeker2_token, hr_token, mock_db):
    # Setup mocks
    mock_save_upload.return_value = {
        "file_path": "uploads/resumes/dummy.pdf",
        "file_url": "/uploads/resumes/dummy.pdf",
        "original_filename": "resume.pdf",
        "file_size_mb": 0.5,
        "mime_type": "application/pdf",
        "extension": ".pdf",
    }
    mock_extract.return_value = {
        "success": True,
        "text": "This is a high quality resume text with experience and skills.",
        "method_used": "pdfplumber",
        "char_count": 60,
    }
    mock_validation_run.return_value = {
        "score": 85,
        "decision": "auto_approved",
        "passed": True,
        "needs_review": False,
        "issues": [],
        "stages": {},
    }

    # Upload resume
    headers = {"Authorization": f"Bearer {seeker1_token}"}
    response = client.post(
        "/api/upload/resume",
        files={"file": ("resume.pdf", DUMMY_PDF_CONTENT, "application/pdf")},
        headers=headers
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["message"] == "Resume uploaded successfully"
    resume_id = json_data["resume_id"]
    assert resume_id is not None

    # Check MongoDB document
    db_resume = mock_db.sync_db["resumes"].find_one({"_id": ObjectId(resume_id)})
    assert db_resume is not None
    assert str(db_resume["user_id"]) == "660000000000000000000001"
    assert db_resume["validation_status"] == "auto_approved"
    assert db_resume["quality_score"] == 85

    # Test GET my-resumes
    response_list = client.get("/api/my-resumes", headers=headers)
    assert response_list.status_code == 200
    assert response_list.json()["total"] == 1
    assert response_list.json()["resumes"][0]["id"] == resume_id

    # Test GET single resume (Owner)
    response_detail = client.get(f"/api/resumes/{resume_id}", headers=headers)
    assert response_detail.status_code == 200
    assert response_detail.json()["id"] == resume_id

    # Test GET single resume (Other Seeker - Unauthorized)
    headers2 = {"Authorization": f"Bearer {seeker2_token}"}
    response_unauthorized = client.get(f"/api/resumes/{resume_id}", headers=headers2)
    assert response_unauthorized.status_code == 403

    # Test GET single resume (HR - Authorized)
    headers_hr = {"Authorization": f"Bearer {hr_token}"}
    response_hr = client.get(f"/api/resumes/{resume_id}", headers=headers_hr)
    assert response_hr.status_code == 200

    # Test DELETE resume (Other Seeker - Unauthorized)
    response_del_unauth = client.delete(f"/api/resumes/{resume_id}", headers=headers2)
    assert response_del_unauth.status_code == 403

    # Test DELETE resume (Owner)
    with patch("app.utils.file_utils.delete_file") as mock_del_file:
        response_del = client.delete(f"/api/resumes/{resume_id}", headers=headers)
        assert response_del.status_code == 200
        assert response_del.json()["message"] == "Resume deleted"
        
        # Verify removed from DB
        assert mock_db.sync_db["resumes"].find_one({"_id": ObjectId(resume_id)}) is None

def test_removed_seeker_endpoints(client, seeker1_token):
    # Verify that the old duplicate seeker endpoints return 404
    headers = {"Authorization": f"Bearer {seeker1_token}"}
    
    assert client.post("/api/seeker/resumes", headers=headers).status_code == 404
    assert client.get("/api/seeker/resumes", headers=headers).status_code == 404
    assert client.get("/api/seeker/resumes/660000000000000000000001", headers=headers).status_code == 404
    assert client.delete("/api/seeker/resumes/660000000000000000000001", headers=headers).status_code == 404
