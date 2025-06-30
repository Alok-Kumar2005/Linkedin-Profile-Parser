import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from src.ai_componenet.database.database import get_db_session
from src.ai_componenet.database.crud import JobDescriptionCRUD, LinkedInCandidateCRUD
from src.ai_componenet.database.models import JobDescription, LinkedInCandidate

class DatabaseQueryUtils:
    """Utility class for common database queries"""
    
    @staticmethod
    def get_job_with_candidates(job_id: int) -> Optional[Dict[str, Any]]:
        """Get job description with all its candidates"""
        with get_db_session() as db:
            job = JobDescriptionCRUD.get_job_description(db, job_id)
            if not job:
                return None
            
            candidates = LinkedInCandidateCRUD.get_candidates_by_job(db, job_id)
            
            return {
                "job": {
                    "id": job.id,
                    "job_title": job.job_title,
                    "company_name": job.company_name,
                    "location": job.job_location,
                    "work_arrangement": job.work_arrangement,
                    "employment_type": job.employment_type,
                    "salary_range": job.salary_range,
                    "experience_required": job.experience_required,
                    "technical_skills": job.technical_skills,
                    "created_at": job.created_at.isoformat() if job.created_at else None
                },
                "candidates": [
                    {
                        "id": candidate.id,
                        "linkedin_url": candidate.linkedin_url,
                        "final_score": candidate.final_score,
                        "education_score": candidate.education_score,
                        "career_trajectory_score": candidate.career_trajectory_score,
                        "company_relevance_score": candidate.company_relevance_score,
                        "experience_match_score": candidate.experience_match_score,
                        "location_match_score": candidate.location_match_score,
                        "tenure_score": candidate.tenure_score,
                        "candidate_name": candidate.candidate_name,
                        "current_position": candidate.current_position,
                        "current_company": candidate.current_company,
                        "is_best_candidate": candidate.is_best_candidate,
                        "created_at": candidate.created_at.isoformat() if candidate.created_at else None
                    }
                    for candidate in candidates
                ]
            }
    
    @staticmethod
    def get_best_candidates_summary() -> List[Dict[str, Any]]:
        """Get summary of all best candidates across all jobs"""
        with get_db_session() as db:
            # Query to get all best candidates with their job details
            query = db.query(LinkedInCandidate, JobDescription).join(
                JobDescription, LinkedInCandidate.job_description_id == JobDescription.id
            ).filter(LinkedInCandidate.is_best_candidate == "Yes")
            
            results = []
            for candidate, job in query.all():
                results.append({
                    "candidate_id": candidate.id,
                    "job_id": job.id,
                    "job_title": job.job_title,
                    "company_name": job.company_name,
                    "candidate_name": candidate.candidate_name,
                    "current_position": candidate.current_position,
                    "current_company": candidate.current_company,
                    "final_score": candidate.final_score,
                    "linkedin_url": candidate.linkedin_url,
                    "created_at": candidate.created_at.isoformat() if candidate.created_at else None
                })
            
            return results
    
    @staticmethod
    def get_job_statistics() -> Dict[str, Any]:
        """Get statistics about jobs and candidates"""
        with get_db_session() as db:
            total_jobs = db.query(JobDescription).count()
            total_candidates = db.query(LinkedInCandidate).count()
            best_candidates = db.query(LinkedInCandidate).filter(
                LinkedInCandidate.is_best_candidate == "Yes"
            ).count()
            
            # Average scores
            avg_score = db.query(LinkedInCandidate.final_score).filter(
                LinkedInCandidate.final_score.isnot(None)
            ).all()
            avg_final_score = sum([score[0] for score in avg_score]) / len(avg_score) if avg_score else 0
            
            return {
                "total_jobs": total_jobs,
                "total_candidates": total_candidates,
                "best_candidates": best_candidates,
                "average_final_score": round(avg_final_score, 2)
            }
