import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from src.ai_componenet.database.models import JobDescription, LinkedInCandidate
from src.ai_componenet.graph.utils.jdinfo import JDInfo

class JobDescriptionCRUD:
    @staticmethod
    def create_job_description(db: Session, jd_info: JDInfo, original_desc: str) -> JobDescription:
        """Create a new job description record"""
        db_job = JobDescription(
            job_title=jd_info.job_title,
            company_name=jd_info.company_name,
            company_description=jd_info.company_description,
            job_location=jd_info.job_location,
            work_arrangement=jd_info.work_arrangement,
            employment_type=jd_info.employment_type,
            salary_range=jd_info.salary_range,
            experience_required=jd_info.experience_required,
            education_requirements=jd_info.education_requirements,
            technical_skills=jd_info.technical_skills,
            soft_skills=jd_info.soft_skills,
            key_responsibilities=jd_info.key_responsibilities,
            job_requirements=jd_info.job_requirements,
            preferred_qualifications=jd_info.preferred_qualifications,
            tools_technologies=jd_info.tools_technologies,
            industry=jd_info.industry,
            seniority_level=jd_info.seniority_level,
            original_job_desc=original_desc
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job
    
    @staticmethod
    def get_job_description(db: Session, job_id: int) -> Optional[JobDescription]:
        """Get job description by ID"""
        return db.query(JobDescription).filter(JobDescription.id == job_id).first()
    
    @staticmethod
    def get_all_job_descriptions(db: Session, skip: int = 0, limit: int = 100) -> List[JobDescription]:
        """Get all job descriptions with pagination"""
        return db.query(JobDescription).offset(skip).limit(limit).all()

class LinkedInCandidateCRUD:
    @staticmethod
    def create_candidate(
        db: Session, 
        job_description_id: int,
        profile_data: str,
        linkedin_url: str = None,
        final_score: float = None,
        score_breakdown: Dict[str, float] = None,
        candidate_name: str = None,
        current_position: str = None,
        current_company: str = None,
        location: str = None,
        is_best_candidate: str = "No",
        outreach_message: str = None
    ) -> LinkedInCandidate:
        """Create a new LinkedIn candidate record"""
        
        # Extract individual scores from breakdown if provided
        education_score = score_breakdown.get("Education", None) if score_breakdown else None
        career_trajectory_score = score_breakdown.get("Career_Trajectory", None) if score_breakdown else None
        company_relevance_score = score_breakdown.get("Company_Relevance", None) if score_breakdown else None
        experience_match_score = score_breakdown.get("Experience_Match", None) if score_breakdown else None
        location_match_score = score_breakdown.get("Location_Match", None) if score_breakdown else None
        tenure_score = score_breakdown.get("Tenure", None) if score_breakdown else None
        
        db_candidate = LinkedInCandidate(
            job_description_id=job_description_id,
            linkedin_url=linkedin_url,
            profile_data=profile_data,
            final_score=final_score,
            education_score=education_score,
            career_trajectory_score=career_trajectory_score,
            company_relevance_score=company_relevance_score,
            experience_match_score=experience_match_score,
            location_match_score=location_match_score,
            tenure_score=tenure_score,
            candidate_name=candidate_name,
            current_position=current_position,
            current_company=current_company,
            location=location,
            is_best_candidate=is_best_candidate,
            outreach_message=outreach_message
        )
        db.add(db_candidate)
        db.commit()
        db.refresh(db_candidate)
        return db_candidate
    
    @staticmethod
    def get_candidates_by_job(db: Session, job_description_id: int) -> List[LinkedInCandidate]:
        """Get all candidates for a specific job"""
        return db.query(LinkedInCandidate).filter(
            LinkedInCandidate.job_description_id == job_description_id
        ).all()
    
    @staticmethod
    def get_best_candidate(db: Session, job_description_id: int) -> Optional[LinkedInCandidate]:
        """Get the best candidate for a specific job"""
        return db.query(LinkedInCandidate).filter(
            LinkedInCandidate.job_description_id == job_description_id,
            LinkedInCandidate.is_best_candidate == "Yes"
        ).first()
    
    @staticmethod
    def update_best_candidate(db: Session, candidate_id: int, outreach_message: str):
        """Update candidate as best candidate with outreach message"""
        candidate = db.query(LinkedInCandidate).filter(LinkedInCandidate.id == candidate_id).first()
        if candidate:
            candidate.is_best_candidate = "Yes"
            candidate.outreach_message = outreach_message
            db.commit()
            db.refresh(candidate)
        return candidate