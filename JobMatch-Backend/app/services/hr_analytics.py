import logging
from bson import ObjectId
from app.utils.helpers import now

logger = logging.getLogger(__name__)


class HRAnalyticsService:
    """
    Feature 13: HR Analytics Dashboard
    Aggregates hiring data into charts and metrics.
    """

    async def get_dashboard(self, db, hr_id) -> dict:
        return {
            "overview":          await self._overview(db, hr_id),
            "applications_by_job": await self._applications_by_job(db, hr_id),
            "score_distribution":  await self._score_distribution(db, hr_id),
            "hiring_funnel":     await self._hiring_funnel(db, hr_id),
            "top_skills_demanded": await self._top_skills(db, hr_id),
            "recent_activity":   await self._recent_activity(db, hr_id),
        }

    async def _overview(self, db, hr_id) -> dict:
        total_jobs       = await db["job_posts"].count_documents({"hr_id": hr_id})
        open_jobs        = await db["job_posts"].count_documents({"hr_id": hr_id, "status": "open"})
        total_rankings   = await db["rankings"].count_documents({"hr_id": hr_id})
        total_shortlisted = await db["shortlists"].count_documents({"hr_id": hr_id})
        total_interviews = await db["interviews"].count_documents({"hr_id": hr_id})

        # Average match score across all rankings
        pipeline = [
            {"$match": {"hr_id": hr_id}},
            {"$unwind": "$candidates_ranked"},
            {"$group": {"_id": None, "avg_score": {"$avg": "$candidates_ranked.score"}}},
        ]
        cursor = db["rankings"].aggregate(pipeline)
        avg_result = await cursor.to_list(length=1)
        avg_score = round(avg_result[0]["avg_score"], 1) if avg_result else 0

        return {
            "total_jobs":         total_jobs,
            "open_jobs":          open_jobs,
            "total_cv_processed": total_rankings,
            "total_shortlisted":  total_shortlisted,
            "total_interviews":   total_interviews,
            "average_match_score": avg_score,
        }

    async def _applications_by_job(self, db, hr_id) -> list:
        pipeline = [
            {"$match": {"hr_id": hr_id}},
            {"$project": {
                "title":          1,
                "total_applicants": {"$size": {"$ifNull": ["$candidates_ranked", []]}},
            }},
            {"$lookup": {
                "from":         "rankings",
                "localField":   "_id",
                "foreignField": "job_id",
                "as":           "ranking_data",
            }},
            {"$addFields": {
                "cv_count": {
                    "$sum": {
                        "$map": {
                            "input": "$ranking_data",
                            "as":    "r",
                            "in":    "$$r.total_cv_processed",
                        }
                    }
                }
            }},
            {"$project": {"title": 1, "cv_count": 1}},
            {"$sort": {"cv_count": -1}},
            {"$limit": 10},
        ]
        cursor = db["job_posts"].aggregate(pipeline)
        results = await cursor.to_list(length=10)
        return [
            {"job_title": r.get("title", "Unknown"), "cv_count": r.get("cv_count", 0)}
            for r in results
        ]

    async def _score_distribution(self, db, hr_id) -> dict:
        pipeline = [
            {"$match": {"hr_id": hr_id}},
            {"$unwind": "$candidates_ranked"},
            {"$bucket": {
                "groupBy": "$candidates_ranked.score",
                "boundaries": [0, 20, 40, 60, 80, 101],
                "default": "other",
                "output": {"count": {"$sum": 1}},
            }},
        ]
        cursor = db["rankings"].aggregate(pipeline)
        results = await cursor.to_list(length=10)

        labels = ["0-20", "20-40", "40-60", "60-80", "80-100"]
        distribution = {l: 0 for l in labels}
        label_map = {0: "0-20", 20: "20-40", 40: "40-60", 60: "60-80", 80: "80-100"}

        for r in results:
            key = label_map.get(r.get("_id"), "other")
            if key in distribution:
                distribution[key] = r["count"]

        return {
            "labels": labels,
            "data":   [distribution[l] for l in labels],
        }

    async def _hiring_funnel(self, db, hr_id) -> dict:
        pipeline_cvs = [
            {"$match": {"hr_id": hr_id}},
            {"$group": {"_id": None, "total": {"$sum": "$total_cv_processed"}}},
        ]
        cursor = db["rankings"].aggregate(pipeline_cvs)
        r = await cursor.to_list(length=1)
        total_cvs = r[0]["total"] if r else 0

        shortlisted  = await db["shortlists"].count_documents({"hr_id": hr_id})
        interviewed  = await db["interviews"].count_documents({"hr_id": hr_id})
        completed    = await db["interviews"].count_documents(
            {"hr_id": hr_id, "status": "completed"}
        )

        return {
            "stages": ["CVs Received", "Shortlisted", "Interviewed", "Completed"],
            "counts": [total_cvs, shortlisted, interviewed, completed],
        }

    async def _top_skills(self, db, hr_id) -> list:
        pipeline = [
            {"$match": {"hr_id": hr_id}},
            {"$project": {"required_skills": 1}},
            {"$unwind": "$required_skills"},
            {"$group": {"_id": "$required_skills", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]
        cursor = db["job_posts"].aggregate(pipeline)
        results = await cursor.to_list(length=10)
        return [{"skill": r["_id"], "count": r["count"]} for r in results]

    async def _recent_activity(self, db, hr_id) -> list:
        pipeline = [
            {"$match": {"hr_id": hr_id}},
            {"$sort": {"created_at": -1}},
            {"$limit": 5},
            {"$project": {"title": 1, "created_at": 1, "status": 1}},
        ]
        cursor = db["job_posts"].aggregate(pipeline)
        results = await cursor.to_list(length=5)
        return [
            {
                "type":       "job_post",
                "title":      r.get("title", ""),
                "status":     r.get("status", ""),
                "created_at": r["created_at"].isoformat() if r.get("created_at") else "",
            }
            for r in results
        ]


hr_analytics_service = HRAnalyticsService()