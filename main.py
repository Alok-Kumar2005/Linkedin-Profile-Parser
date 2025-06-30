from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import sys
import re
import unicodedata
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ai_componenet.graph.proj_graph import create_graph
from src.ai_componenet.database.utils import DatabaseQueryUtils
from src.ai_componenet.exception import CustomException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_text(text):
    """Clean text by removing or replacing problematic characters"""
    if not isinstance(text, str):
        return text
    
    # Replace non-breaking spaces and other problematic unicode characters
    text = text.replace('\xa0', ' ')  # Non-breaking space
    text = text.replace('\u200b', '')  # Zero-width space
    text = text.replace('\u2060', '')  # Word joiner
    text = text.replace('\ufeff', '')  # Byte order mark
    
    # Remove other control characters except common ones (tab, newline, carriage return)
    text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\t\n\r')
    
    # Normalize unicode characters
    text = unicodedata.normalize('NFKC', text)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def clean_data_recursively(data):
    """Recursively clean all string data in nested structures"""
    if isinstance(data, dict):
        return {key: clean_data_recursively(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_data_recursively(item) for item in data]
    elif isinstance(data, str):
        return clean_text(data)
    else:
        return data


def extract_candidate_name(profile_text):
    """Extract candidate name from LinkedIn profile text"""
    if not profile_text:
        return None
    
    lines = profile_text.split('\n')
    for line in lines:
        line = line.strip()
        # Look for lines that might contain the name (usually early in the profile)
        if line and len(line.split()) >= 2 and len(line) < 100:
            # Simple heuristic: if it contains common name patterns
            if any(word.istitle() for word in line.split()):
                # Clean and return the potential name
                name = clean_text(line)
                if name and len(name.split()) >= 2:
                    return name
    return None


def extract_current_position_and_company(profile_text):
    """Extract current position and company from LinkedIn profile text"""
    if not profile_text:
        return None, None
    
    lines = profile_text.split('\n')
    position = None
    company = None
    
    # Look for experience section patterns
    for i, line in enumerate(lines):
        line = line.strip()
        # Look for job titles (usually standalone lines in experience sections)
        if line and 'Present' in lines[i:i+3] if i+3 < len(lines) else []:
            if len(line.split()) <= 8 and not line.startswith('http'):
                position = clean_text(line)
                # Look for company in nearby lines
                for j in range(max(0, i-3), min(len(lines), i+3)):
                    next_line = lines[j].strip()
                    if next_line and next_line != line and len(next_line.split()) <= 6:
                        company = clean_text(next_line)
                        break
                break
    
    return position, company


app = FastAPI(
    title="LinkedIn Profile Parser API",
    description="API for parsing job descriptions and matching LinkedIn profiles",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class JobDescriptionRequest(BaseModel):
    job_desc: str = Field(..., description="The job description text")
    max_profiles: Optional[int] = Field(5, description="Maximum number of profiles to analyze", ge=1, le=10)

class CandidateInfo(BaseModel):
    candidate_id: int
    linkedin_url: Optional[str]
    final_score: float
    score_breakdown: Dict[str, float]
    candidate_name: Optional[str]
    current_position: Optional[str]
    current_company: Optional[str]

class JobMatchResponse(BaseModel):
    job_id: int
    jd_info: Dict[str, Any]
    linkedin_profiles: List[str]
    profiles_found: int
    candidates: List[CandidateInfo]
    best_candidate: Dict[str, Any]
    outreach_message: str
    processing_time: Optional[float]

class DatabaseStatsResponse(BaseModel):
    total_jobs: int
    total_candidates: int
    best_candidates: int
    average_final_score: float

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None

# Initialize the graph
try:
    graph = create_graph()
    logger.info("Graph initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize graph: {str(e)}")
    graph = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "LinkedIn Profile Parser API", 
        "status": "running",
        "graph_status": "initialized" if graph else "failed"
    }

import re
def normalize_whitespace(text: str) -> str:
    """
    Remove extra spaces and newlines from the input text.

    - Replaces any run of whitespace (spaces, tabs, newlines) with a single space.
    - Strips leading and trailing spaces.
    """
    # \s+ matches any sequence of whitespace characters
    cleaned = re.sub(r'\s+', ' ', text)
    return cleaned.strip()



@app.post("/analyze-job", response_model=JobMatchResponse)
async def analyze_job_description(request: JobDescriptionRequest):
    """
    Analyze a job description and find matching LinkedIn profiles
    """
    if not graph:
        raise HTTPException(status_code=500, detail="Graph not initialized")
    
    try:
        import time
        start_time = time.time()
        
        logger.info(f"Processing job description: {request.job_desc[:100]}...")
        
        # Clean the input job description
        cleaned_job_desc = normalize_whitespace(request.job_desc)
        
        # Initialize state for the graph
        initial_state = {
            "job_desc": cleaned_job_desc,
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
        
        # Clean all result data to remove problematic characters
        result = clean_data_recursively(result)
        
        processing_time = time.time() - start_time
        
        # Format candidates data
        candidates = []
        if result.get("candidate_ids") and result.get("fit_score") and result.get("score_breakdown"):
            profile_data_list = result.get("profile_data", [])
            
            for i, candidate_id in enumerate(result["candidate_ids"]):
                # Extract candidate info from profile data
                profile_text = profile_data_list[i] if i < len(profile_data_list) else ""
                candidate_name = extract_candidate_name(profile_text)
                current_position, current_company = extract_current_position_and_company(profile_text)
                
                candidate_info = CandidateInfo(
                    candidate_id=candidate_id,
                    linkedin_url=result["linkedin_profile"][i] if i < len(result["linkedin_profile"]) else None,
                    final_score=result["fit_score"][i],
                    score_breakdown=result["score_breakdown"][i],
                    candidate_name=candidate_name or f"Candidate {i+1}",
                    current_position=current_position,
                    current_company=current_company
                )
                candidates.append(candidate_info)
        
        # Format best candidate data - clean the profile text
        best_candidate_profile_clean = clean_text(result.get("best_candidate_profile", ""))
        best_candidate = {
            "profile": best_candidate_profile_clean,
            "score": result.get("best_candidate_score"),
            "breakdown": result.get("best_candidate_breakdown")
        }
        
        # Format JD info
        jd_info = {}
        if result.get("jd_info"):
            jd_info = {
                "job_title": clean_text(getattr(result["jd_info"], "job_title", "") or ""),
                "company_name": clean_text(getattr(result["jd_info"], "company_name", "") or ""),
                "job_location": clean_text(getattr(result["jd_info"], "job_location", "") or ""),
                "work_arrangement": clean_text(getattr(result["jd_info"], "work_arrangement", "") or ""),
                "employment_type": clean_text(getattr(result["jd_info"], "employment_type", "") or ""),
                "technical_skills": [clean_text(skill) for skill in (getattr(result["jd_info"], "technical_skills", []) or [])],
                "salary_range": clean_text(getattr(result["jd_info"], "salary_range", "") or ""),
                "experience_required": clean_text(getattr(result["jd_info"], "experience_required", "") or "")
            }
        
        # Clean outreach message
        outreach_message_clean = clean_text(result.get("outreach_message", ""))
        
        response = JobMatchResponse(
            job_id=result.get("job_id", 0),
            jd_info=jd_info,
            linkedin_profiles=result.get("linkedin_profile", []),
            profiles_found=result.get("profile_found", 0),
            candidates=candidates,
            best_candidate=best_candidate,
            outreach_message=outreach_message_clean,
            processing_time=round(processing_time, 2)
        )
        
        logger.info(f"Successfully processed job description in {processing_time:.2f} seconds")
        return response
        
    except CustomException as e:
        logger.error(f"Custom exception in analyze_job_description: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Processing error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in analyze_job_description: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/job/{job_id}", response_model=Dict[str, Any])
async def get_job_details(job_id: int):
    """
    Get detailed information about a specific job and its candidates
    """
    try:
        job_data = DatabaseQueryUtils.get_job_with_candidates(job_id)
        
        if not job_data:
            raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
        
        # Clean the job data before returning
        cleaned_job_data = clean_data_recursively(job_data)
        return cleaned_job_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/best-candidates", response_model=List[Dict[str, Any]])
async def get_best_candidates():
    """
    Get summary of all best candidates across all jobs
    """
    try:
        best_candidates = DatabaseQueryUtils.get_best_candidates_summary()
        # Clean the data before returning
        cleaned_candidates = clean_data_recursively(best_candidates)
        return cleaned_candidates
        
    except Exception as e:
        logger.error(f"Error retrieving best candidates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/stats", response_model=DatabaseStatsResponse)
async def get_database_stats():
    """
    Get statistics about jobs and candidates in the database
    """
    try:
        stats = DatabaseQueryUtils.get_job_statistics()
        return DatabaseStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error retrieving database stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/jobs", response_model=List[Dict[str, Any]])
async def get_all_jobs():
    """
    Get a list of all jobs processed
    """
    try:
        # This would need to be implemented in DatabaseQueryUtils
        # For now, return a placeholder
        return [{"message": "This endpoint needs to be implemented in DatabaseQueryUtils"}]
        
    except Exception as e:
        logger.error(f"Error retrieving all jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Error handlers
@app.exception_handler(CustomException)
async def custom_exception_handler(request, exc: CustomException):
    logger.error(f"Custom exception: {str(exc)}")
    return {
        "error": "Processing Error",
        "details": str(exc),
        "status_code": 400
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return {
        "error": "Internal Server Error", 
        "details": "An unexpected error occurred",
        "status_code": 500
    }

if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "main:app",  # Adjust this to your file name
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )