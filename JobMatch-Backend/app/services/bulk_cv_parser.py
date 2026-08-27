import os
import zipfile
import logging
import tempfile
from pathlib import Path
from typing import List
from bson import ObjectId
from fastapi import UploadFile
from app.ml.text_extractor import text_extractor
from app.ml.skill_extractor import skill_extractor
from app.validation.pipeline import validation_pipeline
from app.utils.file_utils import ALLOWED_EXTENSIONS, save_upload
from app.utils.helpers import now

logger = logging.getLogger(__name__)


class BulkCVParserService:
    """
    Feature 8: Bulk CV Upload & Parsing
    Accepts multiple CV files or a ZIP archive.
    Extracts text, validates, and returns parsed results.
    """

    async def parse_multiple(
        self,
        db,
        hr_id,
        job_id: str,
        files: List[UploadFile],
    ) -> dict:
        results = []
        failed = []

        for file in files:
            try:
                result = await self._process_one(db, hr_id, job_id, file)
                if result["success"]:
                    results.append(result)
                else:
                    failed.append(result)
            except Exception as e:
                failed.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e),
                })

        # Save to ranking queue
        for r in results:
            await db["ranking_queue"].update_one(
                {
                    "resume_id": ObjectId(r["resume_id"]),
                    "job_id":    ObjectId(job_id),
                },
                {"$set": {
                    "resume_id":      ObjectId(r["resume_id"]),
                    "job_id":         ObjectId(job_id),
                    "hr_id":          hr_id,
                    "candidate_name": r.get("candidate_name", ""),
                    "filename":       r["filename"],
                    "added_at":       now(),
                }},
                upsert=True,
            )

        return {
            "total_uploaded":   len(files),
            "successfully_parsed": len(results),
            "failed":           len(failed),
            "parsed_resumes":   results,
            "failed_files":     failed,
            "ready_to_rank":    len(results) > 0,
        }

    async def parse_zip(
        self,
        db,
        hr_id,
        job_id: str,
        zip_file: UploadFile,
    ) -> dict:
        """Extract and parse all files from a ZIP archive."""
        results = []
        failed = []

        with tempfile.TemporaryDirectory() as tmpdir:
            # Save ZIP to temp dir
            zip_path = Path(tmpdir) / "upload.zip"
            contents = await zip_file.read()
            with open(zip_path, "wb") as f:
                f.write(contents)

            # Extract ZIP
            try:
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(tmpdir)
            except zipfile.BadZipFile:
                return {"error": "Invalid ZIP file"}

            # Process each extracted file
            for fpath in Path(tmpdir).rglob("*"):
                if fpath.is_file() and fpath.suffix.lower() in ALLOWED_EXTENSIONS:
                    try:
                        result = await self._process_file_path(
                            db, hr_id, job_id, str(fpath), fpath.name
                        )
                        if result["success"]:
                            results.append(result)
                        else:
                            failed.append(result)
                    except Exception as e:
                        failed.append({"filename": fpath.name, "success": False, "error": str(e)})

        return {
            "total_in_zip":     len(results) + len(failed),
            "successfully_parsed": len(results),
            "failed":           len(failed),
            "parsed_resumes":   results,
            "failed_files":     failed,
        }

    async def _process_one(self, db, hr_id, job_id, file: UploadFile) -> dict:
        """Save and process one uploaded file."""
        file_info = await save_upload(file, subfolder="resumes")
        return await self._process_file_path(
            db, hr_id, job_id,
            file_info["file_path"],
            file_info["original_filename"],
            file_info["file_url"],
            file_info["mime_type"],
        )

    async def _process_file_path(
        self, db, hr_id, job_id,
        file_path: str,
        filename: str,
        file_url: str = "",
        mime_type: str = None,
    ) -> dict:
        """Extract text and validate one file."""
        ext = Path(file_path).suffix.lower()

        # Extract text
        extraction = text_extractor.extract(file_path, mime_type)

        if not extraction["success"] or extraction["char_count"] < 100:
            return {
                "filename": filename,
                "success":  False,
                "error":    extraction.get("error", "Text extraction failed"),
                "char_count": extraction["char_count"],
            }

        text = extraction["text"]

        # Extract candidate info
        skills       = skill_extractor.extract(text)
        exp_years    = skill_extractor.extract_experience_years(text)
        education    = skill_extractor.extract_education(text)
        cand_name    = self._extract_name(text)

        # Save resume to DB
        resume_doc = {
            "user_id":          None,
            "uploaded_by_hr":   hr_id,
            "job_id":           ObjectId(job_id) if job_id else None,
            "file_url":         file_url,
            "file_path":        file_path,
            "original_filename": filename,
            "file_type":        ext,
            "extracted_text":   text,
            "skills":           skills,
            "experience_years": exp_years,
            "education":        [e.__dict__ if hasattr(e, '__dict__') else e for e in education],
            "candidate_name":   cand_name,
            "validation_status": "approved",
            "quality_score":    75,
            "uploaded_at":      now(),
        }
        result = await db["resumes"].insert_one(resume_doc)
        resume_id = str(result.inserted_id)

        return {
            "resume_id":       resume_id,
            "filename":        filename,
            "success":         True,
            "candidate_name":  cand_name,
            "skills_found":    skills[:10],
            "experience_years": exp_years,
            "education":       education[:2],
            "char_count":      extraction["char_count"],
            "extraction_method": extraction["method_used"],
        }

    def _extract_name(self, text: str) -> str:
        import re
        lines = text.strip().split("\n")
        for line in lines[:6]:
            line = line.strip()
            match = re.match(r"^([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})$", line)
            if match and 4 < len(line) < 50:
                return match.group(1)
        return "Unknown"


bulk_cv_parser_service = BulkCVParserService()