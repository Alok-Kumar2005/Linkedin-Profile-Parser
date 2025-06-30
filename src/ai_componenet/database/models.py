from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()

class JobDescription(Base):
    __tablename__ = "job_descriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    company_description = Column(Text, nullable=True)
    job_location = Column(String(255), nullable=True)
    work_arrangement = Column(String(50), nullable=True)  # remote, hybrid, onsite, flexible
    employment_type = Column(String(50), nullable=True)  # full-time, part-time, contract, internship, temporary
    salary_range = Column(String(255), nullable=True)
    experience_required = Column(String(255), nullable=True)
    education_requirements = Column(JSON, nullable=True)
    technical_skills = Column(JSON, nullable=True) 
    soft_skills = Column(JSON, nullable=True) 
    key_responsibilities = Column(JSON, nullable=True) 
    job_requirements = Column(JSON, nullable=True) 
    preferred_qualifications = Column(JSON, nullable=True)  
    tools_technologies = Column(JSON, nullable=True) 
    industry = Column(String(255), nullable=True)
    seniority_level = Column(String(50), nullable=True) 
    original_job_desc = Column(Text, nullable=False)  
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to candidates
    candidates = relationship("LinkedInCandidate", back_populates="job_description")


class LinkedInCandidate(Base):
    __tablename__ = "linkedin_candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    linkedin_url = Column(String(500), nullable=True)
    profile_data = Column(Text, nullable=True)  # Raw profile data
    
    # Scoring fields
    final_score = Column(Float, nullable=True)
    education_score = Column(Float, nullable=True)
    career_trajectory_score = Column(Float, nullable=True)
    company_relevance_score = Column(Float, nullable=True)
    experience_match_score = Column(Float, nullable=True)
    location_match_score = Column(Float, nullable=True)
    tenure_score = Column(Float, nullable=True)
    
    # Additional fields that might be extracted from profile
    candidate_name = Column(String(255), nullable=True)
    current_position = Column(String(255), nullable=True)
    current_company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    
    # Metadata
    is_best_candidate = Column(String(10), default="No")  # Yes/No
    outreach_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    job_description = relationship("JobDescription", back_populates="candidates")