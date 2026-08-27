import logging
from datetime import datetime
from bson import ObjectId
from typing import Optional

from app.validation.format_checker import format_checker
from app.validation.spam_detector import spam_detector
from app.validation.quality_scorer import quality_scorer
from app.utils.helpers import now

logger = logging.getLogger(__name__)


class ValidationPipeline:
    """
    Orchestrates all 5 validation stages for every upload.

    Stage 1: Format Check     → file type, size
    Stage 2: Text Extraction  → handled before pipeline (in upload endpoint)
    Stage 3: Quality Scoring  → 0-100 score
    Stage 4: Duplicate Check  → same user same file
    Stage 5: Spam Detection   → spam/gibberish/test uploads

    Routes:
        score  0–39  → auto_rejected  (notify user)
        score 40–69  → pending_review (admin queue)
        score 70–100 → auto_approved  (training pool)
    """

    async def run(
        self,
        db,
        user_id,
        file_path: str,
        file_extension: str,
        extracted_text: Optional[str],
        upload_type: str = "resume",
        file_url: str = "",
    ) -> dict:
        """
        Run all validation stages.
        Returns full pipeline result including final decision.
        """

        stages = {}
        all_issues = []

        # ── Stage 1: Format check ────────────────────────────────
        fmt = format_checker.check(file_path)
        stages["format_check"] = fmt
        if not fmt["passed"]:
            all_issues.extend(fmt["issues"])

        # ── Stage 2: Text check ──────────────────────────────────
        if not extracted_text or len(extracted_text.strip()) < 50:
            stages["text_check"] = {
                "passed": False,
                "issues": ["Could not extract readable text from file"],
            }
            all_issues.append("Text extraction failed or returned empty content")
            # Hard fail — no point scoring empty text
            result = self._build_result(
                score=0,
                decision="auto_rejected",
                stages=stages,
                issues=all_issues,
                rejection_reason="File contains no readable text. Please upload a readable PDF or DOCX.",
            )
            await self._save_to_queue(db, user_id, file_url, upload_type, extracted_text, result)
            return result
        else:
            stages["text_check"] = {"passed": True, "char_count": len(extracted_text)}

        # ── Stage 3: Quality scoring ─────────────────────────────
        quality = quality_scorer.score(extracted_text, file_extension)
        stages["quality_scoring"] = quality
        all_issues.extend(quality.get("reasons", []))

        # ── Stage 4: Duplicate check ─────────────────────────────
        duplicate = await self._check_duplicate(db, user_id, extracted_text)
        stages["duplicate_check"] = duplicate
        if duplicate["is_duplicate"]:
            all_issues.append("This file appears to already be uploaded")

        # ── Stage 5: Spam detection ──────────────────────────────
        spam = spam_detector.check(extracted_text)
        stages["spam_detection"] = spam
        if spam["is_spam"]:
            all_issues.extend(spam["issues"])

        # ── Final score calculation ──────────────────────────────
        base_score = quality["total_score"]

        # Penalties
        if duplicate["is_duplicate"]:
            base_score = max(0, base_score - 15)
        if spam["is_spam"]:
            base_score = max(0, base_score - spam["score_penalty"])
        if not fmt["passed"]:
            base_score = max(0, base_score - 10)

        final_score = min(base_score, 100)

        # Decision
        if final_score >= 70:
            decision = "auto_approved"
        elif final_score >= 40:
            decision = "pending_review"
        else:
            decision = "auto_rejected"

        rejection_reason = None
        if decision == "auto_rejected":
            rejection_reason = self._build_rejection_message(all_issues)

        result = self._build_result(
            score=final_score,
            decision=decision,
            stages=stages,
            issues=all_issues,
            rejection_reason=rejection_reason,
        )

        # Save to validation queue
        queue_id = await self._save_to_queue(
            db, user_id, file_url, upload_type, extracted_text, result
        )
        result["queue_id"] = queue_id

        # If auto-approved → add to training pool
        if decision == "auto_approved":
            await self._add_to_training_pool(
                db, user_id, queue_id, upload_type, extracted_text, final_score
            )

        # Save validation log
        await self._log_validation(db, queue_id, decision, final_score, rejection_reason)

        logger.info(
            f"Validation complete: user={user_id} score={final_score} decision={decision}"
        )

        return result

    # ── Stage 4: Duplicate check ─────────────────────────────────

    async def _check_duplicate(self, db, user_id, text: str) -> dict:
        """Check if same user uploaded the same content recently."""
        try:
            # Use first 500 chars as fingerprint
            fingerprint = text.strip()[:500]
            existing = await db["validation_queue"].find_one({
                "user_id": user_id,
                "text_fingerprint": fingerprint,
            })
            return {
                "is_duplicate": existing is not None,
                "duplicate_id": str(existing["_id"]) if existing else None,
            }
        except Exception as e:
            logger.warning(f"Duplicate check failed: {e}")
            return {"is_duplicate": False, "duplicate_id": None}

    # ── Save to validation queue ─────────────────────────────────

    async def _save_to_queue(
        self, db, user_id, file_url, upload_type, text, result
    ) -> Optional[str]:
        try:
            doc = {
                "upload_type": upload_type,
                "user_id": user_id,
                "file_url": file_url,
                "extracted_text": text,
                "text_fingerprint": (text or "").strip()[:500],
                "quality_score": result["score"],
                "validation_status": result["decision"],
                "rejection_reason": result.get("rejection_reason"),
                "flagged_for_admin": result["decision"] == "pending_review",
                "pipeline_stages": result["stages"],
                "all_issues": result["issues"],
                "uploaded_at": now(),
                "reviewed_by_admin_id": None,
                "reviewed_at": None,
            }
            res = await db["validation_queue"].insert_one(doc)
            return str(res.inserted_id)
        except Exception as e:
            logger.error(f"Failed to save to validation queue: {e}")
            return None

    # ── Add to training pool ─────────────────────────────────────

    async def _add_to_training_pool(
        self, db, user_id, queue_id, upload_type, text, score
    ):
        try:
            doc = {
                "source": "user_upload",
                "source_upload_id": ObjectId(queue_id) if queue_id else None,
                "data_type": upload_type,
                "cleaned_text": text,
                "extracted_skills": [],       # Filled later by ML engine
                "extracted_experience": None,
                "extracted_education": [],
                "quality_score": score,
                "added_to_training_at": now(),
                "used_in_retraining_count": 0,
                "last_used_at": None,
            }
            await db["training_pool"].insert_one(doc)
        except Exception as e:
            logger.error(f"Failed to add to training pool: {e}")

    # ── Save validation log ──────────────────────────────────────

    async def _log_validation(self, db, queue_id, decision, score, reason):
        try:
            await db["validation_logs"].insert_one({
                "upload_id": ObjectId(queue_id) if queue_id else None,
                "action": decision,
                "reason": reason or decision,
                "quality_score_at_time": score,
                "timestamp": now(),
            })
        except Exception as e:
            logger.warning(f"Validation log failed: {e}")

    # ── Helpers ──────────────────────────────────────────────────

    def _build_result(self, score, decision, stages, issues, rejection_reason=None):
        return {
            "score": score,
            "decision": decision,
            "stages": stages,
            "issues": issues,
            "rejection_reason": rejection_reason,
            "passed": decision == "auto_approved",
            "needs_review": decision == "pending_review",
        }

    def _build_rejection_message(self, issues: list) -> str:
        if not issues:
            return "File did not meet quality standards. Please upload a complete resume in PDF or DOCX format."
        msg = "Upload rejected for the following reasons: " + "; ".join(issues[:3])
        msg += ". Please fix these issues and re-upload."
        return msg


validation_pipeline = ValidationPipeline()