from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    location: Optional[str] = None


class EducationItem(BaseModel):
    degree: str
    institution: Optional[str] = None
    year: Optional[str] = None
    field_of_study: Optional[str] = None


class ExperienceItem(BaseModel):
    title: str
    company: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    skills_used: List[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    url: Optional[str] = None


class CandidateProfile(BaseModel):
    name: str
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    cloud_devops: List[str] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    raw_text: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JobProfile(BaseModel):
    job_title: str
    role_level: Optional[str] = None  # Junior, Mid, Senior, Lead, Staff
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    education_requirements: List[str] = Field(default_factory=list)
    min_years_experience: Optional[int] = None
    domain_requirements: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    raw_text: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ResumeUploadResponse(BaseModel):
    resume_id: int
    filename: str
    profile: CandidateProfile


class JobAnalyzeRequest(BaseModel):
    user_id: Optional[int] = None
    title: Optional[str] = None
    job_description_text: str


class JobAnalyzeResponse(BaseModel):
    jd_id: int
    profile: JobProfile
