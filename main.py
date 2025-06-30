from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
from contextlib import asynccontextmanager
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ai_componenet.database.database import get_db_session, create_tables
from src.ai_componenet.database.utils import DatabaseQueryUtils
from src.ai_componenet.database.crud import JobDescriptionCRUD, LinkedInCandidateCRUD
from src.ai_componenet.graph.proj_graph import create_graph
from sqlalchemy.orm import Session

# Pydantic models for request/response
class JobDescriptionRequest(BaseModel):
    job_desc: str
    job_id: Optional[str] = None

class CandidateResponse(BaseModel):
    name: Optional[str]
    linkedin_url: Optional[str]
    fit_score: Optional[float]
    score_breakdown: Optional[Dict[str, float]]
    outreach_message: Optional[str]

class JobAnalysisResponse(BaseModel):
    job_id: str
    candidates_found: int
    top_candidates: List[CandidateResponse]

class DatabaseStatsResponse(BaseModel):
    total_jobs: int
    total_candidates: int
    best_candidates: int
    average_final_score: float

class JobWithCandidatesResponse(BaseModel):
    job: Dict[str, Any]
    candidates: List[Dict[str, Any]]

class BestCandidatesResponse(BaseModel):
    candidates: List[Dict[str, Any]]

# Startup/shutdown context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing database...")
    create_tables()
    print("Database initialized successfully!")
    yield
    # Shutdown
    print("Shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title="LinkedIn Profile Parser API",
    description="API for analyzing job descriptions and finding LinkedIn candidates",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to store the graph
_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = create_graph()
    return _graph

def get_db():
    """Database dependency"""
    with get_db_session() as db:
        yield db

# Background task to process job description
async def process_job_description(job_desc: str, job_id: str = None):
    """Process job description in the background"""
    try:
        graph = get_graph()
        
        # Initialize state
        initial_state = {
            "job_desc": job_desc,
            "jd_info": None,
            "job_id": None,
            "linkedin_profile": None,
            "profile_found": None,
            "profile_data": None,
            "fit_score": None,
            "score_breakdown": None,
            "candidate_ids": None,
            "best_candidate_profile": None,
            "best_candidate_score": None,
            "best_candidate_breakdown": None,
            "outreach_message": None
        }
        
        # Run the workflow
        result = graph.invoke(initial_state)
        return result
        
    except Exception as e:
        print(f"Error processing job description: {str(e)}")
        raise e

# API Endpoints

@app.get("/", summary="Health Check")
async def root():
    """Health check endpoint"""
    return {"message": "LinkedIn Profile Parser API is running", "status": "healthy"}

@app.get("/health", summary="Detailed Health Check")
async def health_check():
    """Detailed health check with database connectivity"""
    try:
        # Test database connection
        stats = DatabaseQueryUtils.get_job_statistics()
        return {
            "status": "healthy",
            "database": "connected",
            "api_version": "1.0.0",
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

@app.post("/analyze-job", response_model=JobAnalysisResponse, summary="Analyze Job Description")
async def analyze_job_description(
    request: JobDescriptionRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze a job description and find matching LinkedIn candidates.
    This processes the job description through the AI pipeline and returns
    formatted results .
    """
    try:
        # Process the job description
        result = await process_job_description(request.job_desc, request.job_id)
        
        # Format the response to match your required structure
        job_id = request.job_id or f"job-{result.get('job_id', 'unknown')}"
        candidates_found = len(result.get("profile_data", [])) if result.get("profile_data") else 0
        
        top_candidates = []
        if result.get("profile_data") and result.get("fit_score") and result.get("score_breakdown"):
            for i, (profile, score, breakdown) in enumerate(zip(
                result["profile_data"], 
                result["fit_score"], 
                result["score_breakdown"]
            )):
                # Extract name from profile data (this would need proper parsing)
                candidate_name = f"Candidate {i+1}"  # Placeholder
                linkedin_url = result.get("linkedin_profile", [None])[i] if i < len(result.get("linkedin_profile", [])) else None
                
                # Format score breakdown to match your structure
                formatted_breakdown = {
                    "education": breakdown.get("Education", 0.0),
                    "trajectory": breakdown.get("Career_Trajectory", 0.0),
                    "company": breakdown.get("Company_Relevance", 0.0),
                    "skills": breakdown.get("Experience_Match", 0.0),
                    "location": breakdown.get("Location_Match", 0.0),
                    "tenure": breakdown.get("Tenure", 0.0)
                }
                
                # Get outreach message for best candidate
                outreach_msg = None
                if i == 0 and result.get("outreach_message"):  # Assuming first is best
                    outreach_msg = result["outreach_message"]
                
                top_candidates.append(CandidateResponse(
                    name=candidate_name,
                    linkedin_url=linkedin_url,
                    fit_score=score,
                    score_breakdown=formatted_breakdown,
                    outreach_message=outreach_msg
                ))
        
        return JobAnalysisResponse(
            job_id=job_id,
            candidates_found=candidates_found,
            top_candidates=top_candidates
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing job description: {str(e)}")


@app.get("/api/jobs/{job_id}", response_model=JobWithCandidatesResponse, summary="Get Job with Candidates")
async def get_job_with_candidates(job_id: int):
    """Get a specific job description with all its candidates"""
    try:
        job_data = DatabaseQueryUtils.get_job_with_candidates(job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobWithCandidatesResponse(**job_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job: {str(e)}")

@app.get("/api/best-candidates", response_model=BestCandidatesResponse, summary="Get All Best Candidates")
async def get_best_candidates():
    """Get summary of all best candidates across all jobs"""
    try:
        candidates = DatabaseQueryUtils.get_best_candidates_summary()
        return BestCandidatesResponse(candidates=candidates)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching best candidates: {str(e)}")

@app.get("/api/jobs", summary="Get All Jobs")
async def get_all_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all job descriptions with pagination"""
    try:
        jobs = JobDescriptionCRUD.get_all_job_descriptions(db, skip=skip, limit=limit)
        return [
            {
                "id": job.id,
                "job_title": job.job_title,
                "company_name": job.company_name,
                "location": job.job_location,
                "work_arrangement": job.work_arrangement,
                "employment_type": job.employment_type,
                "created_at": job.created_at.isoformat() if job.created_at else None
            }
            for job in jobs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")

@app.get("/api/candidates/job/{job_id}", summary="Get Candidates by Job ID")
async def get_candidates_by_job(job_id: int, db: Session = Depends(get_db)):
    """Get all candidates for a specific job"""
    try:
        candidates = LinkedInCandidateCRUD.get_candidates_by_job(db, job_id)
        return [
            {
                "id": candidate.id,
                "linkedin_url": candidate.linkedin_url,
                "candidate_name": candidate.candidate_name,
                "current_position": candidate.current_position,
                "current_company": candidate.current_company,
                "final_score": candidate.final_score,
                "is_best_candidate": candidate.is_best_candidate,
                "created_at": candidate.created_at.isoformat() if candidate.created_at else None
            }
            for candidate in candidates
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching candidates: {str(e)}")

@app.delete("/api/jobs/{job_id}", summary="Delete Job Description")
async def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Delete a job description and all its candidates"""
    try:
        job = JobDescriptionCRUD.get_job_description(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Delete candidates first (due to foreign key constraint)
        candidates = LinkedInCandidateCRUD.get_candidates_by_job(db, job_id)
        for candidate in candidates:
            db.delete(candidate)
        
        # Delete job
        db.delete(job)
        db.commit()
        
        return {"message": f"Job {job_id} and all associated candidates deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)