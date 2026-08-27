from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.utils.helpers import serialize_doc, now
from app.ml.retrainer import model_retrainer
from app.ml.skill_extractor import skill_extractor

router = APIRouter()


def _require_admin(current_user):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")


# ═══════════════════════════════════════════════════════════════
# Validation Queue Management
# ═══════════════════════════════════════════════════════════════

@router.get("/pending-reviews")
async def get_pending_reviews(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    skip: int = 0,
    limit: int = 20,
):
    _require_admin(current_user)
    cursor = db["validation_queue"].find(
        {"validation_status": "pending_review"},
        {"extracted_text": 0},
    ).sort("uploaded_at", -1).skip(skip).limit(limit)

    items = await cursor.to_list(length=limit)
    total = await db["validation_queue"].count_documents(
        {"validation_status": "pending_review"}
    )
    return {
        "items":  [serialize_doc(i) for i in items],
        "total":  total,
        "skip":   skip,
        "limit":  limit,
    }


@router.get("/pending-reviews/{item_id}")
async def get_pending_review_detail(
    item_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_admin(current_user)
    item = await db["validation_queue"].find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return serialize_doc(item)


class ReviewDecision(BaseModel):
    reason: Optional[str] = None


@router.post("/approve/{item_id}")
async def approve_upload(
    item_id: str,
    body: ReviewDecision = ReviewDecision(),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_admin(current_user)
    item = await db["validation_queue"].find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    await db["validation_queue"].update_one(
        {"_id": ObjectId(item_id)},
        {"$set": {
            "validation_status":    "approved",
            "flagged_for_admin":    False,
            "reviewed_by_admin_id": current_user["_id"],
            "reviewed_at":          now(),
        }}
    )

    await db["training_pool"].insert_one({
        "source":              "user_upload",
        "source_upload_id":    ObjectId(item_id),
        "data_type":           item.get("upload_type", "resume"),
        "cleaned_text":        item.get("extracted_text", ""),
        "extracted_skills":    skill_extractor.extract(item.get("extracted_text", "")),
        "extracted_experience": skill_extractor.extract_experience_years(
            item.get("extracted_text", "")
        ),
        "extracted_education": [],
        "quality_score":       item.get("quality_score", 0),
        "added_to_training_at": now(),
        "used_in_retraining_count": 0,
        "last_used_at":        None,
    })

    await db["validation_logs"].insert_one({
        "upload_id":              ObjectId(item_id),
        "action":                 "admin_approve",
        "reason":                 body.reason or "Admin approved",
        "quality_score_at_time":  item.get("quality_score", 0),
        "timestamp":              now(),
    })

    await db["notifications"].insert_one({
        "user_id":     item["user_id"],
        "title":       "Upload Approved ✅",
        "message":     "Your upload was reviewed and approved. Thank you!",
        "type":        "success",
        "read":        False,
        "action_link": None,
        "created_at":  now(),
    })

    return {"message": "Approved and added to training pool"}


@router.post("/reject/{item_id}")
async def reject_upload(
    item_id: str,
    body: ReviewDecision = ReviewDecision(),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_admin(current_user)
    item = await db["validation_queue"].find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    reason = body.reason or "Did not meet quality standards after manual review"

    await db["validation_queue"].update_one(
        {"_id": ObjectId(item_id)},
        {"$set": {
            "validation_status":    "rejected",
            "flagged_for_admin":    False,
            "reviewed_by_admin_id": current_user["_id"],
            "reviewed_at":          now(),
            "rejection_reason":     reason,
        }}
    )

    await db["validation_logs"].insert_one({
        "upload_id":             ObjectId(item_id),
        "action":                "admin_reject",
        "reason":                reason,
        "quality_score_at_time": item.get("quality_score", 0),
        "timestamp":             now(),
    })

    await db["notifications"].insert_one({
        "user_id":     item["user_id"],
        "title":       "Upload Rejected",
        "message":     f"Your upload was rejected: {reason}. Please fix and re-upload.",
        "type":        "warning",
        "read":        False,
        "action_link": None,
        "created_at":  now(),
    })

    return {"message": "Rejected"}


# ═══════════════════════════════════════════════════════════════
# Training Pool
# ═══════════════════════════════════════════════════════════════

@router.get("/training-pool")
async def get_training_pool(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    skip: int = 0,
    limit: int = 20,
    source: Optional[str] = None,
    data_type: Optional[str] = None,
):
    _require_admin(current_user)

    query = {}
    if source:
        query["source"] = source
    if data_type:
        query["data_type"] = data_type

    cursor = db["training_pool"].find(
        query, {"cleaned_text": 0}
    ).sort("added_to_training_at", -1).skip(skip).limit(limit)

    items = await cursor.to_list(length=limit)
    total   = await db["training_pool"].count_documents(query)
    public  = await db["training_pool"].count_documents({"source": "public_dataset"})
    user    = await db["training_pool"].count_documents({"source": "user_upload"})
    resumes = await db["training_pool"].count_documents({"data_type": "resume"})
    jobs    = await db["training_pool"].count_documents({"data_type": "job_description"})

    return {
        "items":                [serialize_doc(i) for i in items],
        "total":                total,
        "public_dataset_count": public,
        "user_upload_count":    user,
        "resume_count":         resumes,
        "job_description_count": jobs,
        "skip":                 skip,
        "limit":                limit,
    }


@router.delete("/training-pool/{item_id}")
async def remove_from_training_pool(
    item_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_admin(current_user)
    await db["training_pool"].delete_one({"_id": ObjectId(item_id)})
    return {"message": "Removed from training pool"}


# ═══════════════════════════════════════════════════════════════
# Model Retraining
# ═══════════════════════════════════════════════════════════════

@router.post("/retrain")
async def trigger_retrain(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_admin(current_user)
    result = await model_retrainer.retrain(db, triggered_by="admin_manual")
    return result


@router.get("/retrain-logs")
async def get_retrain_logs(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    limit: int = 10,
):
    _require_admin(current_user)
    cursor = db["model_retraining_logs"].find({}).sort(
        "retraining_started_at", -1
    ).limit(limit)
    logs = await cursor.to_list(length=limit)
    return [serialize_doc(l) for l in logs]


# ═══════════════════════════════════════════════════════════════
# Validation Statistics
# ═══════════════════════════════════════════════════════════════

@router.get("/validation-stats")
async def get_validation_stats(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_admin(current_user)

    total    = await db["validation_queue"].count_documents({})
    approved = await db["validation_queue"].count_documents(
        {"validation_status": "auto_approved"}
    )
    rejected = await db["validation_queue"].count_documents(
        {"validation_status": "auto_rejected"}
    )
    pending  = await db["validation_queue"].count_documents(
        {"validation_status": "pending_review"}
    )
    adm_app  = await db["validation_queue"].count_documents(
        {"validation_status": "approved"}
    )
    adm_rej  = await db["validation_queue"].count_documents(
        {"validation_status": "rejected"}
    )

    # Score distribution
    pipeline = [
        {"$bucket": {
            "groupBy":    "$quality_score",
            "boundaries": [0, 40, 70, 101],
            "default":    "unknown",
            "output":     {"count": {"$sum": 1}},
        }}
    ]
    cursor = db["validation_queue"].aggregate(pipeline)
    buckets = await cursor.to_list(length=10)
    score_dist = {str(b["_id"]): b["count"] for b in buckets if b["_id"] != "unknown"}

    return {
        "total_uploads":        total,
        "auto_approved":        approved,
        "auto_rejected":        rejected,
        "pending_admin_review": pending,
        "admin_approved":       adm_app,
        "admin_rejected":       adm_rej,
        "auto_approve_rate":    round(approved / max(total, 1) * 100, 1),
        "auto_reject_rate":     round(rejected / max(total, 1) * 100, 1),
        "score_distribution":   score_dist,
    }


# ═══════════════════════════════════════════════════════════════
# Validation Rules
# ═══════════════════════════════════════════════════════════════

class ThresholdUpdate(BaseModel):
    auto_approve_threshold: Optional[int] = None
    auto_reject_threshold:  Optional[int] = None


@router.put("/validation-rules")
async def update_validation_rules(
    body: ThresholdUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_admin(current_user)
    dump_data = body.model_dump() if hasattr(body, "model_dump") else body.dict()
    updates = {k: v for k, v in dump_data.items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No rules to update")

    await db["admin_settings"].update_one(
        {"key": "validation_rules"},
        {"$set": {
            "value":      updates,
            "updated_at": now(),
            "updated_by": current_user["_id"],
        }},
        upsert=True,
    )
    return {"message": "Rules updated", "rules": updates}


@router.get("/validation-rules")
async def get_validation_rules(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_admin(current_user)
    settings = await db["admin_settings"].find_one({"key": "validation_rules"})
    if not settings:
        return {
            "auto_approve_threshold": 70,
            "auto_reject_threshold":  40,
        }
    return settings.get("value", {})


# ═══════════════════════════════════════════════════════════════
# User Management
# ═══════════════════════════════════════════════════════════════

@router.get("/users")
async def list_users(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    role:  Optional[str] = None,
    skip:  int = 0,
    limit: int = 50,
):
    _require_admin(current_user)
    query = {}
    if role:
        query["role"] = role

    cursor = db["users"].find(
        query, {"password_hash": 0}
    ).sort("created_at", -1).skip(skip).limit(limit)

    users = await cursor.to_list(length=limit)
    total = await db["users"].count_documents(query)

    return {
        "users": [serialize_doc(u) for u in users],
        "total": total,
    }


@router.put("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_admin(current_user)
    await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": False}}
    )
    return {"message": "User deactivated"}


@router.put("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_admin(current_user)
    await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": True}}
    )
    return {"message": "User activated"}


# ═══════════════════════════════════════════════════════════════
# Platform Statistics
# ═══════════════════════════════════════════════════════════════

@router.get("/platform-stats")
async def platform_stats(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    _require_admin(current_user)

    seekers  = await db["users"].count_documents({"role": "seeker"})
    hrs      = await db["users"].count_documents({"role": "hr"})
    admins   = await db["users"].count_documents({"role": "admin"})
    resumes  = await db["resumes"].count_documents({})
    jobs     = await db["job_posts"].count_documents({})
    rankings = await db["rankings"].count_documents({})
    pool     = await db["training_pool"].count_documents({})

    # New users last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users = await db["users"].count_documents(
        {"created_at": {"$gte": week_ago}}
    )

    return {
        "users": {
            "total":    seekers + hrs + admins,
            "seekers":  seekers,
            "hr":       hrs,
            "admins":   admins,
            "new_last_7_days": new_users,
        },
        "content": {
            "total_resumes":      resumes,
            "total_job_posts":    jobs,
            "total_rankings":     rankings,
            "training_pool_size": pool,
        },
    }