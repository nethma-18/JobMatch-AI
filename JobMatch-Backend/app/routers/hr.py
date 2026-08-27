from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi import Form
from pydantic import BaseModel
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.utils.helpers import serialize_doc, now
from app.services.job_ranking        import job_ranking_service
from app.services.bulk_cv_parser     import bulk_cv_parser_service
from app.services.hr_analytics       import hr_analytics_service
from app.services.interview_scheduler import interview_scheduler_service
from app.services.blind_screener      import blind_screener_service
from app.ml.skill_extractor          import skill_extractor

router = APIRouter()


def _require_hr(current_user):
    if current_user["role"] not in ("hr", "admin"):
        raise HTTPException(status_code=403, detail="HR access only")


# ═══════════════════════════════════════════════════════════════
# Feature 9 — Job Post Management
# ═══════════════════════════════════════════════════════════════

from app.services.job_description_parser import job_description_parser

class JobPostCreate(BaseModel):
    title:               str
    description:         str
    required_skills:     Optional[List[str]] = []
    preferred_skills:    Optional[List[str]] = []
    experience_required: Optional[float] = None
    education_required:  Optional[str] = None
    employment_type:     Optional[str] = None
    location:            Optional[str] = None
    salary_min:          Optional[float] = None
    salary_max:          Optional[float] = None
    is_template:         Optional[bool] = False
    status:              Optional[str] = "open"


class JobPostUpdate(BaseModel):
    title:               Optional[str] = None
    description:         Optional[str] = None
    required_skills:     Optional[List[str]] = None
    preferred_skills:    Optional[List[str]] = None
    experience_required: Optional[float] = None
    education_required:  Optional[str] = None
    employment_type:     Optional[str] = None
    location:            Optional[str] = None
    salary_min:          Optional[float] = None
    salary_max:          Optional[float] = None
    status:              Optional[str] = None
    is_template:         Optional[bool] = None


def validate_job_payload(title: str, description: str, status: str, experience_required: float, salary_min: float, salary_max: float):
    if not title or len(title.strip()) < 3:
        raise HTTPException(status_code=400, detail="Job title must be at least 3 characters")
    if not description or len(description.strip()) < 50:
        raise HTTPException(status_code=400, detail="Job description must be at least 50 characters")
    if status not in ("draft", "open", "closed"):
        raise HTTPException(status_code=400, detail="Invalid job status. Must be draft, open, or closed")
    if experience_required is not None and experience_required < 0:
        raise HTTPException(status_code=400, detail="Required experience cannot be negative")
    if salary_min is not None and salary_min < 0:
        raise HTTPException(status_code=400, detail="Minimum salary cannot be negative")
    if salary_max is not None and salary_max < 0:
        raise HTTPException(status_code=400, detail="Maximum salary cannot be negative")
    if salary_min is not None and salary_max is not None and salary_max < salary_min:
        raise HTTPException(status_code=400, detail="Maximum salary cannot be less than minimum salary")


@router.post("/jobs", status_code=201)
async def create_job(
    payload: JobPostCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    validate_job_payload(
        title=payload.title,
        description=payload.description,
        status=payload.status or "open",
        experience_required=payload.experience_required,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max
    )

    parsed = job_description_parser.parse(payload.description)

    manual_req = payload.required_skills or []
    parsed_req = parsed.get("required_skills", [])
    merged_req = sorted(list(set(manual_req) | set(parsed_req)))

    manual_pref = payload.preferred_skills or []
    parsed_pref = parsed.get("preferred_skills", [])
    merged_pref = sorted(list(set(manual_pref) | set(parsed_pref)))
    merged_pref = [s for s in merged_pref if s not in merged_req]

    doc = {
        "hr_id":               current_user["_id"],
        "title":               payload.title,
        "company_name":        current_user.get("company_name", ""),
        "description_text":    payload.description,
        "required_skills":     merged_req,
        "preferred_skills":    merged_pref,
        "experience_required": payload.experience_required if payload.experience_required is not None else parsed.get("experience_required"),
        "education_required":  payload.education_required if payload.education_required is not None else parsed.get("education_required"),
        "employment_type":     payload.employment_type if payload.employment_type is not None else parsed.get("employment_type"),
        "location":            payload.location if payload.location is not None else parsed.get("location_type"),
        "salary_range": {
            "min": payload.salary_min,
            "max": payload.salary_max,
            "currency": "USD",
        },
        "status":      payload.status or "open",
        "is_template": payload.is_template or False,
        "created_at":  now(),
        "updated_at":  now(),
    }

    result = await db["job_posts"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return serialize_doc(doc)


@router.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    is_template: Optional[bool] = None,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    _require_hr(current_user)

    query = {"hr_id": current_user["_id"]}
    if status:
        query["status"] = status
    if is_template is not None:
        query["is_template"] = is_template

    cursor = db["job_posts"].find(query).sort("created_at", -1).skip(skip).limit(limit)
    jobs = await cursor.to_list(length=limit)
    total = await db["job_posts"].count_documents(query)

    return {
        "jobs": [serialize_doc(j) for j in jobs],
        "total": total,
    }


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    job = await db["job_posts"].find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return serialize_doc(job)


@router.put("/jobs/{job_id}")
async def update_job(
    job_id: str,
    payload: JobPostUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    existing = await db["job_posts"].find_one({"_id": ObjectId(job_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Job post not found")
    if str(existing["hr_id"]) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    t = payload.title if payload.title is not None else existing.get("title")
    d = payload.description if payload.description is not None else existing.get("description_text")
    st = payload.status if payload.status is not None else existing.get("status")
    exp = payload.experience_required if payload.experience_required is not None else existing.get("experience_required")
    s_min = payload.salary_min if payload.salary_min is not None else existing.get("salary_range", {}).get("min")
    s_max = payload.salary_max if payload.salary_max is not None else existing.get("salary_range", {}).get("max")
    
    validate_job_payload(
        title=t,
        description=d,
        status=st,
        experience_required=exp,
        salary_min=s_min,
        salary_max=s_max
    )

    if payload.description is not None:
        parsed = job_description_parser.parse(payload.description)
        manual_req = payload.required_skills if payload.required_skills is not None else existing.get("required_skills", [])
        parsed_req = parsed.get("required_skills", [])
        merged_req = sorted(list(set(manual_req) | set(parsed_req)))

        manual_pref = payload.preferred_skills if payload.preferred_skills is not None else existing.get("preferred_skills", [])
        parsed_pref = parsed.get("preferred_skills", [])
        merged_pref = sorted(list(set(manual_pref) | set(parsed_pref)))
        merged_pref = [s for s in merged_pref if s not in merged_req]

        updates = {
            "title": t,
            "description_text": d,
            "required_skills": merged_req,
            "preferred_skills": merged_pref,
            "experience_required": exp if payload.experience_required is not None else parsed.get("experience_required"),
            "education_required": payload.education_required if payload.education_required is not None else parsed.get("education_required"),
            "employment_type": payload.employment_type if payload.employment_type is not None else parsed.get("employment_type"),
            "location": payload.location if payload.location is not None else parsed.get("location_type"),
            "salary_range": {
                "min": s_min,
                "max": s_max,
                "currency": "USD",
            },
            "status": st,
            "is_template": payload.is_template if payload.is_template is not None else existing.get("is_template", False),
        }
    else:
        updates = {}
        if payload.title is not None: updates["title"] = payload.title
        if payload.required_skills is not None: updates["required_skills"] = payload.required_skills
        if payload.preferred_skills is not None: updates["preferred_skills"] = payload.preferred_skills
        if payload.experience_required is not None: updates["experience_required"] = payload.experience_required
        if payload.education_required is not None: updates["education_required"] = payload.education_required
        if payload.employment_type is not None: updates["employment_type"] = payload.employment_type
        if payload.location is not None: updates["location"] = payload.location
        if payload.salary_min is not None or payload.salary_max is not None:
            updates["salary_range"] = {
                "min": s_min,
                "max": s_max,
                "currency": "USD"
            }
        if payload.status is not None: updates["status"] = payload.status
        if payload.is_template is not None: updates["is_template"] = payload.is_template

    updates["updated_at"] = now()

    await db["job_posts"].update_one(
        {"_id": ObjectId(job_id)},
        {"$set": updates},
    )
    updated = await db["job_posts"].find_one({"_id": ObjectId(job_id)})
    return serialize_doc(updated)


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    existing = await db["job_posts"].find_one({"_id": ObjectId(job_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Job post not found")
    if str(existing["hr_id"]) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    await db["job_posts"].delete_one({"_id": ObjectId(job_id)})
    return {"message": "Job post deleted"}


@router.post("/jobs/{job_id}/duplicate")
async def duplicate_job(
    job_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Duplicate a job post or template safely without in-memory mutation."""
    _require_hr(current_user)
    job = await db["job_posts"].find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job_copy = dict(job)
    job_copy.pop("_id", None)
    job_copy["title"]      = f"Copy of {job_copy.get('title', '')}"
    job_copy["status"]     = "draft"
    job_copy["created_at"] = now()
    job_copy["updated_at"] = now()

    result = await db["job_posts"].insert_one(job_copy)
    job_copy["_id"] = result.inserted_id
    return serialize_doc(job_copy)


# ═══════════════════════════════════════════════════════════════
# Feature 8 — Bulk CV Upload & Parsing
# ═══════════════════════════════════════════════════════════════

@router.post("/bulk-cv-upload/{job_id}")
async def bulk_cv_upload(
    job_id: str,
    files: List[UploadFile] = File(...),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    # Verify job exists
    job = await db["job_posts"].find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job post not found")

    result = await bulk_cv_parser_service.parse_multiple(
        db, current_user["_id"], job_id, files
    )
    return result


@router.post("/bulk-cv-upload-zip/{job_id}")
async def bulk_cv_upload_zip(
    job_id: str,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Please upload a .zip file")

    result = await bulk_cv_parser_service.parse_zip(
        db, current_user["_id"], job_id, file
    )
    return result


# ═══════════════════════════════════════════════════════════════
# Feature 7 — Job Ranking
# ═══════════════════════════════════════════════════════════════

class RankFromTextRequest(BaseModel):
    jd_text:     str
    top_n:       Optional[int] = 20
    job_id:      Optional[str] = None
    blind_mode:  Optional[bool] = False


@router.post("/job-ranking/{job_id}")
async def rank_job_cvs(
    job_id: str,
    top_n: int = 20,
    blind_mode: bool = False,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Rank all CVs already uploaded for a job with optional blind screening."""
    _require_hr(current_user)
    
    job = await db["job_posts"].find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job post not found")
    if str(job["hr_id"]) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    result = await job_ranking_service.rank_from_db(
        db, current_user["_id"], job_id, top_n=top_n
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    if blind_mode and "rankings" in result:
        result["rankings"] = blind_screener_service.anonymize_rankings(result["rankings"])
        result["blind_mode"] = True

    return result


@router.post("/job-ranking-text")
async def rank_from_text(
    payload: RankFromTextRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Rank resumes directly from text with optional blind screening."""
    _require_hr(current_user)

    # Load resumes from DB for this job
    if payload.job_id:
        cursor = db["ranking_queue"].find({"job_id": payload.job_id})
        queue = await cursor.to_list(length=500)
        resumes = []
        for q in queue:
            r = await db["resumes"].find_one({"_id": q["resume_id"]})
            if r and r.get("extracted_text"):
                resumes.append({
                    "id":       str(r["_id"]),
                    "text":     r["extracted_text"],
                    "filename": r.get("original_filename", ""),
                    "candidate_name": q.get("candidate_name", ""),
                })
    else:
        resumes = []

    if not resumes:
        raise HTTPException(status_code=400, detail="No resumes found. Upload CVs first.")

    result = await job_ranking_service.rank_from_texts(
        db,
        current_user["_id"],
        payload.jd_text,
        resumes,
        job_id=payload.job_id,
        top_n=payload.top_n,
    )

    if payload.blind_mode and "rankings" in result:
        result["rankings"] = blind_screener_service.anonymize_rankings(result["rankings"])
        result["blind_mode"] = True

    return result


@router.get("/rankings/{job_id}")
async def get_rankings(
    job_id: str,
    blind_mode: bool = False,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Get most recent ranking for a job with optional blind screening."""
    job = await db["job_posts"].find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job post not found")
    if str(job["hr_id"]) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    ranking = await db["rankings"].find_one(
        {"job_id": ObjectId(job_id)},
        sort=[("created_at", -1)],
    )
    if not ranking:
        raise HTTPException(status_code=404, detail="No ranking found for this job")

    serialized = serialize_doc(ranking)
    if blind_mode and "candidates_ranked" in serialized:
        serialized["candidates_ranked"] = blind_screener_service.anonymize_rankings(serialized["candidates_ranked"])
        serialized["blind_mode"] = True

    return serialized


# ═══════════════════════════════════════════════════════════════
# Feature 10 — Candidate Shortlisting
# ═══════════════════════════════════════════════════════════════

class ShortlistAction(BaseModel):
    candidate_id: str
    action:       str    # shortlisted | rejected | archived
    rating:       Optional[int] = None     # 1–5
    comment:      Optional[str] = None


class ExportShortlist(BaseModel):
    format: str = "json"   # json | csv


@router.post("/shortlist/{job_id}")
async def shortlist_candidate(
    job_id: str,
    payload: ShortlistAction,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    valid_actions = ["shortlisted", "rejected", "archived"]
    if payload.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Action must be one of: {valid_actions}")

    entry = {
        "candidate_id": ObjectId(payload.candidate_id),
        "status":       payload.action,
        "rating":       payload.rating,
        "comments":     [payload.comment] if payload.comment else [],
        "reviewer_id":  current_user["_id"],
        "actioned_at":  now(),
    }

    await db["shortlists"].update_one(
        {"job_id": ObjectId(job_id), "hr_id": current_user["_id"]},
        {
            "$set":  {"job_id": ObjectId(job_id), "hr_id": current_user["_id"], "updated_at": now()},
            "$pull": {"shortlisted_candidates": {"candidate_id": ObjectId(payload.candidate_id)}},
        },
        upsert=True,
    )
    await db["shortlists"].update_one(
        {"job_id": ObjectId(job_id), "hr_id": current_user["_id"]},
        {"$push": {"shortlisted_candidates": entry}},
    )

    return {"message": f"Candidate {payload.action}", "entry": serialize_doc(entry)}


@router.get("/shortlist/{job_id}")
async def get_shortlist(
    job_id: str,
    status: Optional[str] = None,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    shortlist = await db["shortlists"].find_one({
        "job_id": ObjectId(job_id),
        "hr_id":  current_user["_id"],
    })
    if not shortlist:
        return {"candidates": [], "total": 0}

    candidates = shortlist.get("shortlisted_candidates", [])
    if status:
        candidates = [c for c in candidates if c.get("status") == status]

    return {
        "job_id":     job_id,
        "candidates": [serialize_doc(c) for c in candidates],
        "total":      len(candidates),
        "breakdown": {
            "shortlisted": sum(1 for c in candidates if c.get("status") == "shortlisted"),
            "rejected":    sum(1 for c in candidates if c.get("status") == "rejected"),
            "archived":    sum(1 for c in candidates if c.get("status") == "archived"),
        },
    }


@router.get("/shortlist/{job_id}/export")
async def export_shortlist(
    job_id: str,
    format: str = "json",
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    shortlist = await db["shortlists"].find_one({
        "job_id": ObjectId(job_id),
        "hr_id":  current_user["_id"],
    })
    if not shortlist:
        raise HTTPException(status_code=404, detail="No shortlist found")

    candidates = shortlist.get("shortlisted_candidates", [])
    shortlisted = [c for c in candidates if c.get("status") == "shortlisted"]

    if format == "csv":
        import csv, io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["candidate_id", "status", "rating", "actioned_at"])
        writer.writeheader()
        for c in shortlisted:
            writer.writerow({
                "candidate_id": str(c.get("candidate_id", "")),
                "status":       c.get("status", ""),
                "rating":       c.get("rating", ""),
                "actioned_at":  str(c.get("actioned_at", "")),
            })
        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=shortlist_{job_id}.csv"},
        )

    return {
        "job_id": job_id,
        "shortlisted_candidates": [serialize_doc(c) for c in shortlisted],
        "total": len(shortlisted),
        "exported_at": now().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════
# Feature 11 — Skill Gap Analysis
# ═══════════════════════════════════════════════════════════════

class SkillGapRequest(BaseModel):
    resume_id:  str
    job_id:     Optional[str] = None
    jd_text:    Optional[str] = None
    blind_mode: Optional[bool] = False


@router.post("/skill-gap")
async def skill_gap_analysis(
    payload: SkillGapRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    # 1. Fetch resume and check recruiter authorization (ownership or association)
    resume = await db["resumes"].find_one({"_id": ObjectId(payload.resume_id)})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    authorized = False
    if str(resume.get("user_id")) == str(current_user["_id"]):
        authorized = True
    else:
        my_jobs_cursor = db["job_posts"].find({"hr_id": current_user["_id"]}, {"_id": 1})
        my_job_ids = [doc["_id"] for doc in await my_jobs_cursor.to_list(length=1000)]
        
        if payload.job_id:
            job_obj = await db["job_posts"].find_one({"_id": ObjectId(payload.job_id)})
            if job_obj:
                if str(job_obj["hr_id"]) == str(current_user["_id"]):
                    link = await db["ranking_queue"].find_one({
                        "resume_id": resume["_id"],
                        "job_id": job_obj["_id"]
                    })
                    if link:
                        authorized = True
            else:
                raise HTTPException(status_code=404, detail="Job post not found")
        else:
            link = await db["ranking_queue"].find_one({
                "resume_id": resume["_id"],
                "job_id": {"$in": my_job_ids}
            })
            if link:
                authorized = True

    if not authorized and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # 2. Extract JD text and required/preferred skills
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
    else:
        required_skills = skill_extractor.extract(jd_text) if jd_text else []

    if not jd_text:
        raise HTTPException(status_code=400, detail="Provide job_id or jd_text")

    # Normalize skill names (casing)
    resume_text = resume.get("extracted_text", "")
    resume_skills = set(s.lower() for s in skill_extractor.extract(resume_text))
    required_set = set(s.lower() for s in required_skills)
    preferred_set = set(s.lower() for s in preferred_skills)

    # 3. Match Required Skills
    matched_req = list(resume_skills & required_set)
    missing_req = list(required_set - resume_skills)

    if len(required_set) > 0:
        coverage_pct = round((len(matched_req) / len(required_set)) * 100, 1)
    else:
        coverage_pct = 100.0

    def priority(skill):
        try:
            return jd_text.lower().index(skill.lower())
        except ValueError:
            return 9999

    missing_req_prioritized = sorted(missing_req, key=priority)

    # 4. Match Preferred Skills
    matched_pref = list(resume_skills & preferred_set)
    missing_pref = list(preferred_set - resume_skills)
    missing_pref_prioritized = sorted(missing_pref, key=priority)

    # 5. Extra Candidate Skills
    extra = list(resume_skills - required_set - preferred_set)
    extra_prioritized = sorted(extra, key=priority)

    # 6. Gap Severity classification
    if len(required_set) == 0:
        severity = "Not Applicable"
    else:
        missing_count = len(missing_req)
        total_count = len(required_set)
        missing_ratio = missing_count / total_count
        if missing_count == 0:
            severity = "None"
        elif missing_ratio <= 0.20:
            severity = "Low"
        elif missing_ratio <= 0.40:
            severity = "Medium"
        elif missing_ratio <= 0.60:
            severity = "High"
        else:
            severity = "Critical"

    # 7. Experience Comparison
    cand_exp = skill_extractor.extract_experience_years(resume_text)
    exp_gap = None
    exp_status = "unknown"
    if exp_required is not None and exp_required > 0:
        if cand_exp is not None:
            exp_gap = max(0.0, float(exp_required) - float(cand_exp))
            exp_status = "meets_requirement" if cand_exp >= exp_required else "below_requirement"
    else:
        exp_status = "meets_requirement"

    # 8. Education Comparison
    def extract_degree(text: str) -> Optional[str]:
        import re
        text_lower = text.lower()
        if re.search(r"\b(ph\.?d\.?|doctorate)\b", text_lower):
            return "PhD"
        if re.search(r"\b(master['\s]?s?|m\.?sc?\.?|m\.?eng\.?|m\.?a\.?|mba)\b", text_lower):
            return "Master's"
        if re.search(r"\b(bachelor['\s]?s?|b\.?sc?\.?|b\.?eng\.?|b\.?a\.?)\b", text_lower):
            return "Bachelor's"
        if re.search(r"\b(diploma|associate)\b", text_lower):
            return "Associate / Diploma"
        return None

    cand_edu = extract_degree(resume_text)
    edu_match = "unknown"
    if edu_required:
        if cand_edu:
            levels = {
                "phd": 4,
                "master's": 3,
                "bachelor's": 2,
                "associate / diploma": 1
            }
            req_level = levels.get(edu_required.lower(), 0)
            cand_level = levels.get(cand_edu.lower(), 0)
            if req_level == 0 or cand_level == 0:
                edu_match = str(edu_required.lower() == cand_edu.lower())
            else:
                edu_match = str(cand_level >= req_level).lower()
        else:
            edu_match = "unknown"
    else:
        edu_match = "true"

    if edu_match == "true":
        edu_match_val = True
    elif edu_match == "false":
        edu_match_val = False
    else:
        edu_match_val = "unknown"

    # 9. Recommendation message
    recommendation = (
        f"Strong candidate — only {len(missing_req)} skills missing."
        if len(missing_req) <= 2 else
        f"Moderate gap — missing {len(missing_req)} skills: {', '.join(missing_req_prioritized[:3])}."
        if len(missing_req) <= 5 else
        f"Significant gap — {len(missing_req)} required skills absent. Consider other candidates."
    )

    # 10. Blind mode anonymization
    candidate_name = resume.get("candidate_name", "Unknown")
    filename = resume.get("original_filename", "Unknown")
    if payload.blind_mode:
        candidate_name = "Candidate"
        filename = "Resume_Candidate.pdf"
        recommendation = blind_screener_service.sanitize_text(recommendation)

    return {
        # Flat compatibility fields
        "candidate_name":    candidate_name,
        "resume_id":         str(resume["_id"]),
        "match_percentage":  coverage_pct,
        "matched_skills":    matched_req,
        "missing_skills":    missing_req_prioritized,
        "additional_skills": extra_prioritized[:10],
        "total_required":    len(required_set),
        "total_matched":     len(matched_req),
        "total_missing":     len(missing_req),
        "gap_severity":      severity,
        "recommendation":    recommendation,
        "filename":          filename,

        # New structured format fields
        "candidate_id":      str(resume["_id"]),
        "job_id":            str(payload.job_id) if payload.job_id else None,
        "required_skills": {
            "matched": matched_req,
            "missing": missing_req_prioritized,
            "coverage_percentage": coverage_pct
        },
        "preferred_skills": {
            "matched": matched_pref,
            "missing": missing_pref_prioritized
        },
        "extra_skills":      extra_prioritized[:10],
        "experience": {
            "required": float(exp_required) if exp_required is not None else None,
            "candidate": float(cand_exp) if cand_exp is not None else None,
            "gap": float(exp_gap) if exp_gap is not None else None,
            "status": exp_status
        },
        "education": {
            "required": edu_required,
            "candidate": cand_edu,
            "match": edu_match_val
        }
    }


# ═══════════════════════════════════════════════════════════════
# Feature 12 — Interview Scheduler
# ═══════════════════════════════════════════════════════════════

class ScheduleInterviewRequest(BaseModel):
    candidate_id:     str
    job_id:           Optional[str] = None
    scheduled_date:   datetime
    duration_minutes: Optional[int] = 60
    meeting_link:     Optional[str] = None
    notes:            Optional[str] = None


class UpdateInterviewRequest(BaseModel):
    status:   str
    feedback: Optional[str] = None


@router.post("/interviews")
async def schedule_interview(
    payload: ScheduleInterviewRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    dump_data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    result = await interview_scheduler_service.schedule(
        db, current_user["_id"], dump_data
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/interviews")
async def list_interviews(
    job_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    return await interview_scheduler_service.list_interviews(
        db, current_user["_id"], job_id, status
    )


@router.get("/interviews/upcoming")
async def upcoming_interviews(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    return await interview_scheduler_service.get_upcoming(db, current_user["_id"])


@router.put("/interviews/{interview_id}")
async def update_interview(
    interview_id: str,
    payload: UpdateInterviewRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    return await interview_scheduler_service.update_status(
        db, current_user["_id"], interview_id, payload.status, payload.feedback
    )


# ═══════════════════════════════════════════════════════════════
# Feature 13 — HR Analytics Dashboard
# ═══════════════════════════════════════════════════════════════

@router.get("/analytics")
async def hr_analytics(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    return await hr_analytics_service.get_dashboard(db, current_user["_id"])


# ═══════════════════════════════════════════════════════════════
# Feature 14 — Collaborative Hiring
# ═══════════════════════════════════════════════════════════════

class AddTeamMember(BaseModel):
    member_email: str
    role:         str = "reviewer"    # reviewer | admin


class AddComment(BaseModel):
    candidate_id: str
    comment:      str
    rating:       Optional[int] = None   # 1–5


class CastVote(BaseModel):
    candidate_id: str
    vote:         str   # hire | reject | maybe


@router.post("/team-members")
async def add_team_member(
    payload: AddTeamMember,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    member = await db["users"].find_one({"email": payload.member_email})
    if not member:
        raise HTTPException(status_code=404, detail="User not found with that email")

    await db["hr_profiles"].update_one(
        {"user_id": current_user["_id"]},
        {"$addToSet": {
            "team_members": {
                "member_user_id": member["_id"],
                "email":          payload.member_email,
                "role":           payload.role,
                "added_at":       now(),
            }
        }},
        upsert=True,
    )

    # Notify new team member
    await db["notifications"].insert_one({
        "user_id":     member["_id"],
        "title":       "Added to Hiring Team",
        "message":     f"You have been added to {current_user.get('name', 'an HR team')} as a {payload.role}.",
        "type":        "info",
        "read":        False,
        "action_link": None,
        "created_at":  now(),
    })

    return {"message": f"{payload.member_email} added as {payload.role}"}


@router.get("/team-members")
async def get_team_members(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)
    profile = await db["hr_profiles"].find_one({"user_id": current_user["_id"]})
    if not profile:
        return {"team_members": []}
    return {"team_members": serialize_doc(profile).get("team_members", [])}


@router.post("/comment/{job_id}")
async def add_comment(
    job_id: str,
    payload: AddComment,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    comment_doc = {
        "reviewer_id":   current_user["_id"],
        "reviewer_name": current_user.get("name", "HR"),
        "comment":       payload.comment,
        "rating":        payload.rating,
        "commented_at":  now(),
    }

    await db["candidate_reviews"].update_one(
        {
            "job_id":       ObjectId(job_id),
            "candidate_id": ObjectId(payload.candidate_id),
        },
        {
            "$set":  {
                "job_id":       ObjectId(job_id),
                "candidate_id": ObjectId(payload.candidate_id),
            },
            "$push": {"comments": comment_doc},
        },
        upsert=True,
    )

    return {"message": "Comment added", "comment": serialize_doc(comment_doc)}


@router.get("/comments/{job_id}/{candidate_id}")
async def get_comments(
    job_id: str,
    candidate_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    review = await db["candidate_reviews"].find_one({
        "job_id":       ObjectId(job_id),
        "candidate_id": ObjectId(candidate_id),
    })
    if not review:
        return {"comments": [], "votes": {}}

    return serialize_doc(review)


@router.post("/vote/{job_id}")
async def cast_vote(
    job_id: str,
    payload: CastVote,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_hr(current_user)

    valid_votes = ["hire", "reject", "maybe"]
    if payload.vote not in valid_votes:
        raise HTTPException(status_code=400, detail=f"Vote must be: {valid_votes}")

    vote_key = f"votes.{str(current_user['_id'])}"

    await db["candidate_reviews"].update_one(
        {
            "job_id":       ObjectId(job_id),
            "candidate_id": ObjectId(payload.candidate_id),
        },
        {
            "$set": {
                "job_id":       ObjectId(job_id),
                "candidate_id": ObjectId(payload.candidate_id),
                vote_key:       payload.vote,
            }
        },
        upsert=True,
    )

    # Tally votes
    review = await db["candidate_reviews"].find_one({
        "job_id":       ObjectId(job_id),
        "candidate_id": ObjectId(payload.candidate_id),
    })
    votes = review.get("votes", {}) if review else {}
    tally = {"hire": 0, "reject": 0, "maybe": 0}
    for v in votes.values():
        if v in tally:
            tally[v] += 1

    return {"message": "Vote recorded", "tally": tally}