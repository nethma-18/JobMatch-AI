from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ValidationStatus(str, Enum):
    pending = "pending"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    auto_approved = "auto_approved"
    auto_rejected = "auto_rejected"


class EducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[int] = None


class ResumeResponse(BaseModel):
    id: str
    user_id: str
    file_url: str
    original_filename: str
    file_type: str
    extracted_text: Optional[str] = None
    skills: List[str] = []
    experience_years: Optional[float] = None
    education: List[EducationItem] = []
    ats_score: Optional[float] = None
    validation_status: ValidationStatus = ValidationStatus.pending
    quality_score: Optional[float] = None
    uploaded_at: datetime


class ResumeListResponse(BaseModel):
    resumes: List[ResumeResponse]
    total: int


class ExtractionResult(BaseModel):
    success: bool
    text: Optional[str] = None
    method_used: str
    char_count: int = 0
    error: Optional[str] = None