import logging
from bson import ObjectId
from datetime import datetime, timedelta
from app.utils.helpers import serialize_doc, now

logger = logging.getLogger(__name__)


class InterviewSchedulerService:
    """
    Feature 12: Interview Scheduler
    Schedule interviews, track status, send notifications.
    """

    VALID_STATUSES = ["pending", "confirmed", "completed", "cancelled", "rescheduled"]

    async def schedule(self, db, hr_id, data: dict) -> dict:
        candidate_id  = data.get("candidate_id")
        job_id        = data.get("job_id")
        scheduled_date = data.get("scheduled_date")
        duration       = data.get("duration_minutes", 60)
        meeting_link   = data.get("meeting_link", "")
        notes          = data.get("notes", "")

        if not candidate_id or not scheduled_date:
            return {"error": "candidate_id and scheduled_date are required"}

        # Generate a Google Calendar-style link
        calendar_link = self._generate_calendar_link(
            title=f"Interview - Job {job_id}",
            start=scheduled_date,
            duration_minutes=duration,
            meeting_link=meeting_link,
        )

        doc = {
            "job_id":           ObjectId(job_id) if job_id else None,
            "candidate_id":     ObjectId(candidate_id) if candidate_id else None,
            "hr_id":            hr_id,
            "scheduled_date":   scheduled_date,
            "duration_minutes": duration,
            "calendar_link":    calendar_link,
            "meeting_link":     meeting_link,
            "status":           "pending",
            "notes":            notes,
            "reminder_sent":    False,
            "feedback":         None,
            "created_at":       now(),
        }

        result = await db["interviews"].insert_one(doc)
        doc["_id"] = result.inserted_id

        # Notify candidate (if they have an account)
        await self._notify_candidate(db, candidate_id, doc)

        return serialize_doc(doc)

    async def list_interviews(
        self,
        db,
        hr_id,
        job_id: str = None,
        status: str = None,
    ) -> list:
        query = {"hr_id": hr_id}
        if job_id:
            query["job_id"] = ObjectId(job_id)
        if status:
            query["status"] = status

        cursor = db["interviews"].find(query).sort("scheduled_date", 1)
        items = await cursor.to_list(length=200)
        return [serialize_doc(i) for i in items]

    async def update_status(
        self,
        db,
        hr_id,
        interview_id: str,
        status: str,
        feedback: str = None,
    ) -> dict:
        if status not in self.VALID_STATUSES:
            return {"error": f"Invalid status. Use: {self.VALID_STATUSES}"}

        updates = {"status": status, "updated_at": now()}
        if feedback:
            updates["feedback"] = feedback

        await db["interviews"].update_one(
            {"_id": ObjectId(interview_id), "hr_id": hr_id},
            {"$set": updates},
        )
        updated = await db["interviews"].find_one({"_id": ObjectId(interview_id)})
        return serialize_doc(updated)

    async def get_upcoming(self, db, hr_id) -> list:
        """Get interviews scheduled in next 7 days."""
        now_dt = datetime.utcnow()
        next_week = now_dt + timedelta(days=7)

        cursor = db["interviews"].find({
            "hr_id": hr_id,
            "scheduled_date": {"$gte": now_dt, "$lte": next_week},
            "status": {"$in": ["pending", "confirmed"]},
        }).sort("scheduled_date", 1)

        items = await cursor.to_list(length=50)
        return [serialize_doc(i) for i in items]

    def _generate_calendar_link(
        self,
        title: str,
        start: datetime,
        duration_minutes: int,
        meeting_link: str,
    ) -> str:
        """Generate Google Calendar event link."""
        if not start:
            return ""
        fmt = "%Y%m%dT%H%M%SZ"
        start_str = start.strftime(fmt) if isinstance(start, datetime) else ""
        end_dt = start + timedelta(minutes=duration_minutes) if isinstance(start, datetime) else start
        end_str = end_dt.strftime(fmt)

        title_encoded = title.replace(" ", "+")
        details = f"Meeting+link:+{meeting_link}" if meeting_link else ""

        return (
            f"https://calendar.google.com/calendar/render"
            f"?action=TEMPLATE"
            f"&text={title_encoded}"
            f"&dates={start_str}/{end_str}"
            f"&details={details}"
        )

    async def _notify_candidate(self, db, candidate_id: str, interview_doc: dict):
        """Create in-app notification for the candidate."""
        try:
            # Find user with this resume
            resume = await db["resumes"].find_one({"_id": ObjectId(candidate_id)})
            if resume and resume.get("user_id"):
                scheduled = interview_doc.get("scheduled_date")
                date_str = scheduled.strftime("%B %d, %Y at %H:%M UTC") if isinstance(scheduled, datetime) else "TBD"
                await db["notifications"].insert_one({
                    "user_id":     resume["user_id"],
                    "title":       "Interview Scheduled",
                    "message":     f"An interview has been scheduled for you on {date_str}.",
                    "type":        "info",
                    "read":        False,
                    "action_link": interview_doc.get("meeting_link", ""),
                    "created_at":  now(),
                })
        except Exception as e:
            logger.warning(f"Could not notify candidate: {e}")


interview_scheduler_service = InterviewSchedulerService()