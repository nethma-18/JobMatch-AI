import logging
from bson import ObjectId
from app.utils.helpers import serialize_doc, now

logger = logging.getLogger(__name__)


class JobTrackerService:
    """
    Feature 5: Job Tracker Dashboard
    Full CRUD for tracking job applications.
    """

    VALID_STATUSES = ["applied", "interview", "offer", "rejected", "withdrawn"]

    async def create(self, db, user_id, data: dict) -> dict:
        doc = {
            "seeker_id": user_id,
            "job_title":      data.get("job_title", ""),
            "company":        data.get("company", ""),
            "job_url":        data.get("job_url", ""),
            "status":         data.get("status", "applied"),
            "applied_date":   data.get("applied_date") or now(),
            "interview_date": data.get("interview_date"),
            "salary_expected": data.get("salary_expected"),
            "location":       data.get("location", ""),
            "notes":          data.get("notes", ""),
            "resume_used":    data.get("resume_used", ""),
            "contact_person": data.get("contact_person", ""),
            "follow_up_date": data.get("follow_up_date"),
            "created_at":     now(),
            "updated_at":     now(),
        }

        result = await db["applications"].insert_one(doc)
        doc["_id"] = result.inserted_id
        return serialize_doc(doc)

    async def list_all(self, db, user_id, status_filter=None) -> list:
        query = {"seeker_id": user_id}
        if status_filter:
            query["status"] = status_filter

        cursor = db["applications"].find(query).sort("applied_date", -1)
        items = await cursor.to_list(length=200)
        return [serialize_doc(i) for i in items]

    async def get_one(self, db, user_id, application_id: str) -> dict:
        item = await db["applications"].find_one({
            "_id": ObjectId(application_id),
            "seeker_id": user_id,
        })
        return serialize_doc(item) if item else None

    async def update(self, db, user_id, application_id: str, data: dict) -> dict:
        updates = {k: v for k, v in data.items() if v is not None}
        updates["updated_at"] = now()

        await db["applications"].update_one(
            {"_id": ObjectId(application_id), "seeker_id": user_id},
            {"$set": updates}
        )
        return await self.get_one(db, user_id, application_id)

    async def delete(self, db, user_id, application_id: str) -> bool:
        result = await db["applications"].delete_one({
            "_id": ObjectId(application_id),
            "seeker_id": user_id,
        })
        return result.deleted_count > 0

    async def get_stats(self, db, user_id) -> dict:
        pipeline = [
            {"$match": {"seeker_id": user_id}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        cursor = db["applications"].aggregate(pipeline)
        results = await cursor.to_list(length=20)

        stats = {s: 0 for s in self.VALID_STATUSES}
        for r in results:
            stats[r["_id"]] = r["count"]
        stats["total"] = sum(stats.values())

        return stats


job_tracker_service = JobTrackerService()