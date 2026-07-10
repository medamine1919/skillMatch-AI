from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EducationItem(BaseModel):
    degree: str = ""
    field: str = ""
    institution: str = ""
    start_date: str = ""
    end_date: str = ""


class ExperienceItem(BaseModel):
    job_title: str = ""
    company: str = ""
    start_date: str = ""
    end_date: str = ""
    duration_months: int = 0
    description: str = ""
    skills_used: list[str] = Field(default_factory=list)


class CVSchema(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    summary: str = ""
    skills_technical: list[str] = Field(default_factory=list)
    skills_soft: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    teaching_signals: list[str] = Field(default_factory=list)
    mentoring_signals: list[str] = Field(default_factory=list)
    youth_education_signals: list[str] = Field(default_factory=list)
    estimated_years_experience: float = 0.0


class RequirementSchema(BaseModel):
    input_mode: str = ""
    job_title: str = ""
    contract_type: str = ""
    location: str = ""
    target_sector: str = "IT / e-learning"
    required_speciality: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    languages_required: list[str] = Field(default_factory=list)
    experience_required_years: float = 0.0
    education_requirements: list[str] = Field(default_factory=list)
    teaching_required: bool = False
    mentoring_preferred: bool = False
    audience_type: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    priority_criteria: list[str] = Field(default_factory=list)
