from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from datetime import datetime
from bson import ObjectId

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.utils.file_utils import save_upload, delete_file
from app.utils.helpers import serialize_doc, now
from app.ml.text_extractor import text_extractor
from app.validation.pipeline import validation_pipeline

router = APIRouter()


# ── Upload resume ────────────────────────────────────────────────

@router.post("/upload/resume")
async def upload_resume(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    # Save file
    file_info = await save_upload(file, subfolder="resumes")

    # Extract text immediately
    extraction = text_extractor.extract(
        file_info["file_path"],
        mime_type=file_info["mime_type"],
    )

    resume_doc = {
        "user_id": current_user["_id"],
        "file_url": file_info["file_url"],
        "file_path": file_info["file_path"],
        "original_filename": file_info["original_filename"],
        "file_type": file_info["extension"],
        "file_size_mb": file_info["file_size_mb"],
        "mime_type": file_info["mime_type"],
        "extracted_text": extraction["text"] if extraction["success"] else None,
        "extraction_method": extraction["method_used"],
        "extraction_success": extraction["success"],
        "char_count": extraction["char_count"],
        "skills": [],
        "experience_years": None,
        "education": [],
        "ats_score": None,
        "validation_status": "pending",
        "quality_score": None,
        "uploaded_at": now(),
    }

    result = await db["resumes"].insert_one(resume_doc)
    resume_doc["_id"] = result.inserted_id

    # Run validation pipeline
    validation_result = await validation_pipeline.run(
        db=db,
        user_id=current_user["_id"],
        file_path=file_info["file_path"],
        file_extension=file_info["extension"],
        extracted_text=extraction["text"] if extraction["success"] else None,
        upload_type="resume",
        file_url=file_info["file_url"],
    )

    # Update resume doc with validation result
    await db["resumes"].update_one(
        {"_id": result.inserted_id},
        {"$set": {
            "validation_status": validation_result["decision"],
            "quality_score": validation_result["score"],
        }}
    )

    return {
        "message": "Resume uploaded successfully",
        "resume_id": str(result.inserted_id),
        "extraction": {
            "success": extraction["success"],
            "method_used": extraction["method_used"],
            "char_count": extraction["char_count"],
            "error": extraction.get("error"),
        },
        "validation": {
            "score": validation_result["score"],
            "decision": validation_result["decision"],
            "passed": validation_result["passed"],
            "needs_review": validation_result["needs_review"],
            "rejection_reason": validation_result.get("rejection_reason"),
            "issues": validation_result["issues"],
        },
        "resume": serialize_doc(resume_doc),
    }


# ── Upload job description ───────────────────────────────────────

@router.post("/upload/job-description")
async def upload_job_description(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    if current_user["role"] not in ("hr", "admin"):
        raise HTTPException(status_code=403, detail="HR or admin only")

    file_info = await save_upload(file, subfolder="job_descriptions")

    extraction = text_extractor.extract(
        file_info["file_path"],
        mime_type=file_info["mime_type"],
    )

    jd_doc = {
        "hr_id": current_user["_id"],
        "file_url": file_info["file_url"],
        "file_path": file_info["file_path"],
        "original_filename": file_info["original_filename"],
        "file_type": file_info["extension"],
        "extracted_text": extraction["text"] if extraction["success"] else None,
        "extraction_success": extraction["success"],
        "char_count": extraction["char_count"],
        "uploaded_at": now(),
    }

    result = await db["job_descriptions"].insert_one(jd_doc)
    jd_doc["_id"] = result.inserted_id

    # Optionally run validation for job descriptions too
    # validation_result = await validation_pipeline.run(
    #     db=db,
    #     user_id=current_user["_id"],
    #     file_path=file_info["file_path"],
    #     file_extension=file_info["extension"],
    #     extracted_text=extraction["text"] if extraction["success"] else None,
    #     upload_type="job_description",
    #     file_url=file_info["file_url"],
    # )

    return {
        "message": "Job description uploaded",
        "jd_id": str(result.inserted_id),
        "extraction": {
            "success": extraction["success"],
            "method_used": extraction["method_used"],
            "char_count": extraction["char_count"],
        },
        "job_description": serialize_doc(jd_doc),
    }


# ── Get my resumes ───────────────────────────────────────────────

@router.get("/my-resumes")
async def get_my_resumes(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    cursor = db["resumes"].find(
        {"user_id": current_user["_id"]},
        {"extracted_text": 0, "file_path": 0},   # Exclude heavy fields
    ).sort("uploaded_at", -1)

    resumes = await cursor.to_list(length=50)
    return {
        "resumes": [serialize_doc(r) for r in resumes],
        "total": len(resumes),
    }


# ── Get single resume ────────────────────────────────────────────

@router.get("/resumes/{resume_id}")
async def get_resume(
    resume_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    resume = await db["resumes"].find_one({"_id": ObjectId(resume_id)})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Owners and admins can view
    is_owner = str(resume["user_id"]) == str(current_user["_id"])
    is_admin = current_user["role"] == "admin"
    is_hr = current_user["role"] == "hr"

    if not (is_owner or is_admin or is_hr):
        raise HTTPException(status_code=403, detail="Access denied")

    return serialize_doc(resume)


# ── Delete resume ────────────────────────────────────────────────

@router.delete("/resumes/{resume_id}")
async def delete_resume(
    resume_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    resume = await db["resumes"].find_one({"_id": ObjectId(resume_id)})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if str(resume["user_id"]) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Delete file from disk
    if resume.get("file_path"):
        delete_file(resume["file_path"])

    await db["resumes"].delete_one({"_id": ObjectId(resume_id)})

    return {"message": "Resume deleted"}


# ── Notifications ────────────────────────────────────────────────

@router.get("/notifications")
async def get_notifications(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    skip: int = 0,
    limit: int = 20,
):
    cursor = db["notifications"].find(
        {"user_id": current_user["_id"]}
    ).sort("created_at", -1).skip(skip).limit(limit)

    notifications = await cursor.to_list(length=limit)
    unread_count = await db["notifications"].count_documents(
        {"user_id": current_user["_id"], "read": False}
    )

    return {
        "notifications": [serialize_doc(n) for n in notifications],
        "unread_count": unread_count,
    }


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    await db["notifications"].update_one(
        {"_id": ObjectId(notification_id), "user_id": current_user["_id"]},
        {"$set": {"read": True}},
    )
    return {"message": "Marked as read"}


@router.put("/notifications/read-all")
async def mark_all_read(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await db["notifications"].update_many(
        {"user_id": current_user["_id"], "read": False},
        {"$set": {"read": True}},
    )
    return {"message": f"{result.modified_count} notifications marked as read"}