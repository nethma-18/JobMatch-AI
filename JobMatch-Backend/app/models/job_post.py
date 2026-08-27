from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    open = "open"
    closed = "closed"
    draft = "draft"


class SalaryRange(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    currency: str = "USD"


class JobPostCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=50)
    required_skills: List[str] = []
    experience_required: Optional[float] = None
    location: Optional[str] = None
    salary_range: Optional[SalaryRange] = None
    is_template: bool = False


class JobPostUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    experience_required: Optional[float] = None
    location: Optional[str] = None
    salary_range: Optional[SalaryRange] = None
    status: Optional[JobStatus] = None
    is_template: Optional[bool] = None


class JobPostResponse(BaseModel):
    id: str
    hr_id: str
    title: str
    description: str
    required_skills: List[str] = []
    experience_required: Optional[float] = None
    location: Optional[str] = None
    salary_range: Optional[SalaryRange] = None
    status: JobStatus
    is_template: bool
    created_at: datetime