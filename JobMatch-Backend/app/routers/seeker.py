from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.utils.helpers import serialize_doc
from app.services.resume_enhancer    import resume_enhancer_service
from app.services.ats_checker        import ats_checker_service
from app.services.rejection_diagnostic import rejection_diagnostic_service
from app.services.cover_letter       import cover_letter_service
from app.services.interview_questions import interview_questions_service
from app.services.job_tracker        import job_tracker_service

router = APIRouter()


def _require_seeker(current_user):
    if current_user["role"] not in ("seeker", "admin"):
        raise HTTPException(status_code=403, detail="Seeker access only")


# ═══════════════════════════════════════════════════════════════
# Feature 1 — Resume Enhancer
# ═══════════════════════════════════════════════════════════════

class ResumeEnhancerRequest(BaseModel):
    resume_id:  str
    job_id:     Optional[str] = None
    jd_text:    Optional[str] = None      # Paste JD text directly
    jd_id:      Optional[str] = None      # Or use uploaded JD id


@router.post("/resume-enhancer")
async def resume_enhancer(
    payload: ResumeEnhancerRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_seeker(current_user)
    from app.ml.skill_extractor import skill_extractor

    # Load resume text
    resume = await db["resumes"].find_one({"_id": ObjectId(payload.resume_id)})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Security check: Seekers can only access their own resumes
    if str(resume.get("user_id")) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    resume_text = resume.get("extracted_text", "")
    if not resume_text:
        raise HTTPException(status_code=400, detail="Resume has no extracted text. Re-upload a readable file.")

    # Load JD text & details
    jd_text = payload.jd_text
    required_skills = []
    preferred_skills = []
    exp_required = None
    edu_required = None

    if not jd_text and payload.job_id:
        job = await db["job_posts"].find_one({"_id": ObjectId(payload.job_id)})
        if job:
            jd_text = job.get("description_text", "")
            required_skills = job.get("required_skills", [])
            preferred_skills = job.get("preferred_skills", [])
            exp_required = job.get("experience_required")
            edu_required = job.get("education_required")
        else:
            raise HTTPException(status_code=404, detail="Job post not found")
            
    elif not jd_text and payload.jd_id:
        jd_doc = await db["job_descriptions"].find_one({"_id": ObjectId(payload.jd_id)})
        if jd_doc:
            jd_text = jd_doc.get("extracted_text", "")
            required_skills = skill_extractor.extract(jd_text) if jd_text else []
        else:
            raise HTTPException(status_code=404, detail="Job description upload not found")

    if not jd_text:
        raise HTTPException(status_code=400, detail="Provide job_id, jd_id, or jd_text")

    result = resume_enhancer_service.analyze(
        resume_text=resume_text,
        jd_text=jd_text,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        exp_required=exp_required,
        edu_required=edu_required
    )

    # Save result to DB
    await db["resume_analyses"].insert_one({
        "user_id": current_user["_id"],
        "resume_id": ObjectId(payload.resume_id),
        "feature": "resume_enhancer",
        "result": result,
        "created_at": datetime.utcnow(),
    })

    return result


# ═══════════════════════════════════════════════════════════════
# Feature 6 — ATS Checker
# ═══════════════════════════════════════════════════════════════

class ATSCheckRequest(BaseModel):
    resume_id:  str
    job_id:     Optional[str] = None
    jd_text:    Optional[str] = None


@router.post("/ats-checker")
async def ats_checker(
    payload: ATSCheckRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_seeker(current_user)

    resume = await db["resumes"].find_one({"_id": ObjectId(payload.resume_id)})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Security: Seekers can only ATS check their own resumes
    if str(resume.get("user_id")) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    resume_text = resume.get("extracted_text", "")
    if not resume_text:
        raise HTTPException(status_code=400, detail="No text extracted from resume")

    jd_text = payload.jd_text
    if not jd_text and payload.job_id:
        job = await db["job_posts"].find_one({"_id": ObjectId(payload.job_id)})
        if job:
            jd_text = job.get("description_text", "")
        else:
            raise HTTPException(status_code=404, detail="Job post not found")

    result = ats_checker_service.check(
        resume_text,
        file_extension=resume.get("file_type", ".pdf"),
        jd_text=jd_text
    )
    result["resume_id"] = str(resume["_id"])

    # Save ATS report
    await db["ats_reports"].update_one(
        {"resume_id": ObjectId(payload.resume_id)},
        {"$set": {
            "resume_id":   ObjectId(payload.resume_id),
            "score":       result["ats_score"],
            "grade":       result["grade"],
            "checks":      result["breakdown"], # Keep flat scores mapping
            "breakdown":   result["breakdown"],
            "suggestions": result["suggestions"],
            "checked_at":  datetime.utcnow(),
        }},
        upsert=True,
    )

    # Update resume doc
    await db["resumes"].update_one(
        {"_id": ObjectId(payload.resume_id)},
        {"$set": {"ats_score": result["ats_score"]}},
    )

    return result


# ═══════════════════════════════════════════════════════════════
# Feature 4 — Rejection Diagnostic
# ═══════════════════════════════════════════════════════════════

class DiagnosticRequest(BaseModel):
    resume_id: str
    jd_text: Optional[str] = None
    jd_id:   Optional[str] = None


@router.post("/rejection-diagnostic")
async def rejection_diagnostic(
    payload: DiagnosticRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_seeker(current_user)

    resume = await db["resumes"].find_one({"_id": ObjectId(payload.resume_id)})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_text = resume.get("extracted_text", "")
    jd_text = payload.jd_text

    if not jd_text and payload.jd_id:
        jd_doc = await db["job_descriptions"].find_one({"_id": ObjectId(payload.jd_id)})
        if jd_doc:
            jd_text = jd_doc.get("extracted_text", "")

    if not jd_text:
        raise HTTPException(status_code=400, detail="Provide jd_text or a valid jd_id")

    result = rejection_diagnostic_service.diagnose(resume_text, jd_text)

    await db["diagnostics"].insert_one({
        "user_id":   current_user["_id"],
        "resume_id": ObjectId(payload.resume_id),
        "result":    result,
        "created_at": datetime.utcnow(),
    })

    return result


# ═══════════════════════════════════════════════════════════════
# Feature 2 — Cover Letter Generator
# ═══════════════════════════════════════════════════════════════

class CoverLetterRequest(BaseModel):
    resume_id:      str
    job_id:         Optional[str] = None
    jd_text:        Optional[str] = None
    jd_id:          Optional[str] = None
    company_name:   Optional[str] = "the company"
    job_title:      Optional[str] = "this position"
    applicant_name: Optional[str] = "Applicant"
    tone:           Optional[str] = "professional"  # professional | enthusiastic | concise


@router.post("/cover-letter")
async def generate_cover_letter(
    payload: CoverLetterRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_seeker(current_user)

    resume = await db["resumes"].find_one({"_id": ObjectId(payload.resume_id)})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Security check: Seeker owns their resume
    if str(resume.get("user_id")) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    resume_text = resume.get("extracted_text", "")
    if not resume_text:
        raise HTTPException(status_code=400, detail="Resume has no extracted text.")

    jd_text = payload.jd_text
    company_name = payload.company_name
    job_title = payload.job_title
    required_skills = []
    preferred_skills = []
    exp_required = None
    edu_required = None

    if not jd_text and payload.job_id:
        job = await db["job_posts"].find_one({"_id": ObjectId(payload.job_id)})
        if job:
            jd_text = job.get("description_text", "")
            company_name = job.get("company_name", company_name)
            job_title = job.get("title", job_title)
            required_skills = job.get("required_skills", [])
            preferred_skills = job.get("preferred_skills", [])
            exp_required = job.get("experience_required")
            edu_required = job.get("education_required")
        else:
            raise HTTPException(status_code=404, detail="Job post not found")
            
    elif not jd_text and payload.jd_id:
        jd_doc = await db["job_descriptions"].find_one({"_id": ObjectId(payload.jd_id)})
        if jd_doc:
            jd_text = jd_doc.get("extracted_text", "")
        else:
            raise HTTPException(status_code=404, detail="Job description not found")

    if not jd_text:
        raise HTTPException(status_code=400, detail="Provide job_id, jd_id, or jd_text")

    tone = payload.tone if payload.tone in cover_letter_service.TONES else "professional"

    result = cover_letter_service.generate(
        resume_text=resume_text,
        jd_text=jd_text,
        applicant_name=payload.applicant_name,
        company_name=company_name,
        job_title=job_title,
        tone=tone,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        exp_required=exp_required,
        edu_required=edu_required
    )

    # Save generated letter
    saved = await db["cover_letters"].insert_one({
        "user_id":          current_user["_id"],
        "resume_id":        ObjectId(payload.resume_id),
        "generated_text":   result["cover_letter"],
        "user_edited_text": None,
        "tone":             tone,
        "company_name":     result["company_name"],
        "job_title":        result["job_title"],
        "matched_skills":   result["matched_skills_used"],
        "experience_used":  result["relevant_experience_used"],
        "metadata":         result["generation_metadata"],
        "created_at":       datetime.utcnow(),
        "downloaded":       False,
    })

    result["cover_letter_id"] = str(saved.inserted_id)
    return result


@router.put("/cover-letter/{letter_id}")
async def update_cover_letter(
    letter_id: str,
    body: dict,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Save user-edited version of generated cover letter."""
    _require_seeker(current_user)
    
    letter = await db["cover_letters"].find_one({"_id": ObjectId(letter_id)})
    if not letter:
        raise HTTPException(status_code=404, detail="Cover letter not found")
        
    if str(letter["user_id"]) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    edited_text = body.get("edited_text", "")
    await db["cover_letters"].update_one(
        {"_id": ObjectId(letter_id)},
        {"$set": {"user_edited_text": edited_text, "downloaded": True}},
    )
    return {"message": "Cover letter saved"}


# ═══════════════════════════════════════════════════════════════
# Feature 3 — Interview Question Generator
# ═══════════════════════════════════════════════════════════════

class InterviewQRequest(BaseModel):
    resume_id:     str
    job_id:        Optional[str] = None
    jd_text:       Optional[str] = None
    jd_id:         Optional[str] = None
    num_questions: Optional[int] = 12


@router.post("/interview-questions")
async def generate_interview_questions(
    payload: InterviewQRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_seeker(current_user)

    num_q = payload.num_questions if payload.num_questions is not None else 12
    if num_q < 5 or num_q > 20:
        raise HTTPException(status_code=400, detail="Number of questions must be between 5 and 20")

    resume = await db["resumes"].find_one({"_id": ObjectId(payload.resume_id)})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Security check: Seeker owns their resume
    if str(resume.get("user_id")) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    resume_text = resume.get("extracted_text", "")
    if not resume_text:
        raise HTTPException(status_code=400, detail="Resume has no extracted text.")

    jd_text = payload.jd_text
    required_skills = []
    preferred_skills = []
    exp_required = None
    edu_required = None

    if not jd_text and payload.job_id:
        job = await db["job_posts"].find_one({"_id": ObjectId(payload.job_id)})
        if job:
            jd_text = job.get("description_text", "")
            required_skills = job.get("required_skills", [])
            preferred_skills = job.get("preferred_skills", [])
            exp_required = job.get("experience_required")
            edu_required = job.get("education_required")
        else:
            raise HTTPException(status_code=404, detail="Job post not found")

    elif not jd_text and payload.jd_id:
        jd_doc = await db["job_descriptions"].find_one({"_id": ObjectId(payload.jd_id)})
        if jd_doc:
            jd_text = jd_doc.get("extracted_text", "")
        else:
            raise HTTPException(status_code=404, detail="Job description not found")

    if not jd_text:
        raise HTTPException(status_code=400, detail="Provide job_id, jd_id, or jd_text")

    result = interview_questions_service.generate(
        resume_text=resume_text,
        jd_text=jd_text,
        num_questions=num_q,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        exp_required=exp_required,
        edu_required=edu_required
    )

    await db["interview_question_sets"].insert_one({
        "user_id":   current_user["_id"],
        "resume_id": ObjectId(payload.resume_id),
        "result":    result,
        "created_at": datetime.utcnow(),
    })

    return result


# ═══════════════════════════════════════════════════════════════
# Feature 5 — Job Tracker Dashboard
# ═══════════════════════════════════════════════════════════════

class ApplicationCreate(BaseModel):
    job_title:       str
    company:         str
    job_url:         Optional[str] = None
    status:          Optional[str] = "applied"
    applied_date:    Optional[datetime] = None
    interview_date:  Optional[datetime] = None
    salary_expected: Optional[float] = None
    location:        Optional[str] = None
    notes:           Optional[str] = None
    resume_used:     Optional[str] = None
    contact_person:  Optional[str] = None
    follow_up_date:  Optional[datetime] = None


class ApplicationUpdate(BaseModel):
    job_title:       Optional[str] = None
    company:         Optional[str] = None
    status:          Optional[str] = None
    interview_date:  Optional[datetime] = None
    notes:           Optional[str] = None
    follow_up_date:  Optional[datetime] = None
    salary_expected: Optional[float] = None


@router.post("/applications", status_code=201)
async def create_application(
    payload: ApplicationCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_seeker(current_user)
    dump_data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    return await job_tracker_service.create(db, current_user["_id"], dump_data)


@router.get("/applications")
async def list_applications(
    status: Optional[str] = None,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_seeker(current_user)
    return {
        "applications": await job_tracker_service.list_all(db, current_user["_id"], status),
        "stats": await job_tracker_service.get_stats(db, current_user["_id"]),
    }


@router.get("/applications/{application_id}")
async def get_application(
    application_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_seeker(current_user)
    item = await job_tracker_service.get_one(db, current_user["_id"], application_id)
    if not item:
        raise HTTPException(status_code=404, detail="Application not found")
    return item


@router.put("/applications/{application_id}")
async def update_application(
    application_id: str,
    payload: ApplicationUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_seeker(current_user)
    dump_data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    updated = await job_tracker_service.update(
        db, current_user["_id"], application_id, dump_data
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found")
    return updated


@router.delete("/applications/{application_id}")
async def delete_application(
    application_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_seeker(current_user)
    deleted = await job_tracker_service.delete(db, current_user["_id"], application_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Application deleted"}


@router.get("/applications-stats")
async def application_stats(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_seeker(current_user)
    return await job_tracker_service.get_stats(db, current_user["_id"])


# ═══════════════════════════════════════════════════════════════
# Profile Management
# ═══════════════════════════════════════════════════════════════

@router.get("/profile")
async def get_profile(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_seeker(current_user)
    profile = await db["seeker_profiles"].find_one({"user_id": current_user["_id"]})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return {
        "user": serialize_doc(current_user),
        "profile": serialize_doc(profile)
    }

@router.put("/profile")
async def update_profile(
    payload: dict,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_seeker(current_user)
    
    update_data = {k: v for k, v in payload.items() if k not in ("_id", "user_id", "created_at")}
    
    if update_data:
        await db["seeker_profiles"].update_one(
            {"user_id": current_user["_id"]},
            {"$set": update_data}
        )
    
    updated = await db["seeker_profiles"].find_one({"user_id": current_user["_id"]})
    return serialize_doc(updated)


@router.get("/jobs")
async def list_open_jobs(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_seeker(current_user)
    cursor = db["job_posts"].find({"status": "open"}, {"title": 1, "company_name": 1, "description_text": 1})
    jobs = await cursor.to_list(length=100)
    return {"jobs": [serialize_doc(j) for j in jobs]}