import logging
import asyncio
from typing import List, Optional
from bson import ObjectId
from app.ml.similarity import similarity_engine
from app.ml.text_extractor import text_extractor
from app.ml.skill_extractor import skill_extractor
from app.utils.helpers import serialize_doc, now

logger = logging.getLogger(__name__)


class JobRankingService:
    """
    Feature 7: Job Ranking
    Ranks 500+ CVs against a job description.
    Processes in async batches for performance.
    """

    BATCH_SIZE = 50  # Process CVs in batches

    async def rank_from_db(self, db, hr_id, job_id: str, top_n: int = 20) -> dict:
        job = await db["job_posts"].find_one({"_id": ObjectId(job_id)})
        if not job:
            return {"error": "Job post not found"}

        jd_text = job.get("description_text", "")
        if not jd_text:
            return {"error": "Job description has no text"}

        required_skills = job.get("required_skills", [])
        preferred_skills = job.get("preferred_skills", [])

        # ← Query with ObjectId, not string
        cursor = db["ranking_queue"].find({"job_id": ObjectId(job_id)})
        resume_docs = await cursor.to_list(length=1000)

        if not resume_docs:
            return {"error": "No resumes found for this job. Upload CVs first."}

        resumes = []
        for doc in resume_docs:
            # resume_id stored as ObjectId in ranking_queue
            rid = doc.get("resume_id")
            if not rid:
                continue
            resume_doc = await db["resumes"].find_one({"_id": rid})
            if resume_doc and resume_doc.get("extracted_text"):
                resumes.append({
                    "id":             str(rid),
                    "text":           resume_doc["extracted_text"],
                    "filename":       resume_doc.get("original_filename", "Unknown"),
                    "candidate_name": doc.get("candidate_name", ""),
                })

        if not resumes:
            return {"error": "CVs were uploaded but text extraction failed. Check file formats."}

        return await self._run_ranking(db, hr_id, job_id, jd_text, resumes, required_skills, preferred_skills, top_n)

    async def rank_from_texts(
        self,
        db,
        hr_id,
        jd_text: str,
        resumes: List[dict],   # [{id, text, filename, candidate_name}]
        job_id: Optional[str] = None,
        top_n: int = 20,
    ) -> dict:
        """
        Rank resumes provided directly as text.
        Used when HR uploads everything in one request.
        """
        required_skills = []
        preferred_skills = []
        if job_id:
            job = await db["job_posts"].find_one({"_id": ObjectId(job_id)})
            if job:
                required_skills = job.get("required_skills", [])
                preferred_skills = job.get("preferred_skills", [])
        return await self._run_ranking(db, hr_id, job_id, jd_text, resumes, required_skills, preferred_skills, top_n)

    async def _run_ranking(self, db, hr_id, job_id, jd_text, resumes, required_skills, preferred_skills, top_n):
        if not resumes:
            return {"error": "No valid resumes to rank"}

        start_time = asyncio.get_event_loop().time()

        # Run similarity ranking
        ranked = similarity_engine.rank_resumes(
            jd_text=jd_text,
            resumes=resumes,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            top_n=top_n,
        )

        elapsed = round(asyncio.get_event_loop().time() - start_time, 2)

        # Save ranking result to DB
        ranking_doc = {
            "job_id":              ObjectId(job_id) if job_id else None,
            "hr_id":               hr_id,
            "candidates_ranked":   ranked,
            "total_cv_processed":  len(resumes),
            "top_n_returned":      len(ranked),
            "processing_time_sec": elapsed,
            "created_at":          now(),
        }
        result = await db["rankings"].insert_one(ranking_doc)

        return {
            "ranking_id":          str(result.inserted_id),
            "job_id":              str(job_id) if job_id else None,
            "total_cv_processed":  len(resumes),
            "total_ranked":        len(ranked),
            "processing_time_sec": elapsed,
            "rankings":            ranked,
            "jd_skills":           required_skills or skill_extractor.extract(jd_text),
        }


job_ranking_service = JobRankingService()