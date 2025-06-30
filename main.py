from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Dict, Any, Optional
import asyncio
from contextlib import asynccontextmanager
import sys
import json
import traceback
import re
import unicodedata
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ai_componenet.database.database import get_db_session, create_tables
from src.ai_componenet.database.utils import DatabaseQueryUtils
from src.ai_componenet.database.crud import JobDescriptionCRUD, LinkedInCandidateCRUD
from src.ai_componenet.graph.proj_graph import create_graph
from sqlalchemy.orm import Session

# Enhanced utility functions for JSON serialization
def deep_clean_text(text):
    """Comprehensive text cleaning for JSON serialization"""
    if not isinstance(text, str):
        return text
    
    try:
        # Step 1: Replace specific problematic characters first
        # Non-breaking space (\xa0) and other common problematic characters
        replacements = {
            '\xa0': ' ',  # Non-breaking space - THIS IS THE MAIN CULPRIT
            '\u00a0': ' ',  # Another representation of non-breaking space
            '\u2000': ' ',  # En quad
            '\u2001': ' ',  # Em quad
            '\u2002': ' ',  # En space
            '\u2003': ' ',  # Em space
            '\u2004': ' ',  # Three-per-em space
            '\u2005': ' ',  # Four-per-em space
            '\u2006': ' ',  # Six-per-em space
            '\u2007': ' ',  # Figure space
            '\u2008': ' ',  # Punctuation space
            '\u2009': ' ',  # Thin space
            '\u200a': ' ',  # Hair space
            '\u200b': '',   # Zero width space
            '\u200c': '',   # Zero width non-joiner
            '\u200d': '',   # Zero width joiner
            '\u2060': '',   # Word joiner
            '\ufeff': '',   # Zero width no-break space (BOM)
            '\r\n': ' ',
            '\r': ' ',
            '\n': ' ',
            '\t': ' ',
            '\x0b': ' ',    # Vertical tab
            '\x0c': ' ',    # Form feed
            '\u2028': ' ',  # Line separator
            '\u2029': ' ',  # Paragraph separator
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Step 2: Normalize unicode characters
        text = unicodedata.normalize('NFKC', text)
        
        # Step 3: Remove remaining control characters (C0 and C1 control codes)
        # This includes \x00-\x1f and \x7f-\x9f ranges
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')
        
        # Step 4: Remove any remaining problematic bytes
        # Convert to bytes and back to catch any remaining issues
        text = text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
        
        # Step 5: Collapse multiple whitespace into single space
        text = re.sub(r'\s+', ' ', text)
        
        # Step 6: Strip leading/trailing whitespace
        text = text.strip()
        
        # Step 7: Final validation - try to encode as JSON string
        try:
            json.dumps(text)
        except (UnicodeDecodeError, UnicodeEncodeError):
            # If still problematic, convert to ASCII
            text = text.encode('ascii', errors='ignore').decode('ascii')
        
        return text
        
    except Exception as e:
        print(f"Error cleaning text: {e}")
        # Return a safe fallback
        try:
            return str(text).encode('ascii', errors='ignore').decode('ascii')
        except:
            return "<<text_cleaning_failed>>"

def safe_serialize_value(obj):
    """Safely serialize a single value to JSON-compatible format"""
    if obj is None:
        return None
    elif isinstance(obj, bool):
        return obj
    elif isinstance(obj, (int, float)):
        # Handle special float values
        if isinstance(obj, float):
            if obj != obj:  # NaN check
                return None
            elif obj == float('inf'):
                return "Infinity"
            elif obj == float('-inf'):
                return "-Infinity"
        return obj
    elif isinstance(obj, str):
        return deep_clean_text(obj)
    elif isinstance(obj, (datetime, Decimal)):
        return str(obj)
    elif isinstance(obj, bytes):
        try:
            return obj.decode('utf-8', errors='ignore')
        except:
            return obj.hex()
    elif hasattr(obj, '__dict__'):
        # Handle custom objects like JDInfo by converting to dict
        try:
            if hasattr(obj, '_asdict'):
                # Handle namedtuples
                return obj._asdict()
            elif hasattr(obj, 'dict'):
                # Handle Pydantic models
                return obj.dict()
            elif hasattr(obj, '__dict__'):
                # Handle regular objects
                return {k: safe_serialize_value(v) for k, v in obj.__dict__.items()}
            else:
                return deep_clean_text(str(obj))
        except:
            return deep_clean_text(str(obj))
    else:
        # For any other type, convert to string and clean
        try:
            return deep_clean_text(str(obj))
        except:
            return "<<serialization_error>>"

def deep_safe_serialize(obj, max_depth=10, current_depth=0):
    """Recursively and safely serialize any object to JSON-compatible format"""
    # Prevent infinite recursion
    if current_depth > max_depth:
        return "<<max_depth_exceeded>>"
    
    if obj is None:
        return None
    elif isinstance(obj, dict):
        cleaned_dict = {}
        for key, value in obj.items():
            try:
                # Clean the key
                clean_key = safe_serialize_value(key) if not isinstance(key, str) else deep_clean_text(key)
                # Clean the value recursively
                clean_value = deep_safe_serialize(value, max_depth, current_depth + 1)
                cleaned_dict[clean_key] = clean_value
            except Exception as e:
                print(f"Error serializing dict item {key}: {e}")
                cleaned_dict[str(key)] = f"<<serialization_error: {str(e)}>>"
        return cleaned_dict
    elif isinstance(obj, (list, tuple, set)):
        cleaned_list = []
        for i, item in enumerate(obj):
            try:
                clean_item = deep_safe_serialize(item, max_depth, current_depth + 1)
                cleaned_list.append(clean_item)
            except Exception as e:
                print(f"Error serializing list item {i}: {e}")
                cleaned_list.append(f"<<serialization_error: {str(e)}>>")
        return cleaned_list
    else:
        return safe_serialize_value(obj)

def validate_json_response(data):
    """Validate that data can be safely serialized to JSON"""
    try:
        # First, deeply clean the data
        cleaned_data = deep_safe_serialize(data)
        
        # Try to serialize and parse to catch any remaining issues
        json_str = json.dumps(cleaned_data, ensure_ascii=False, indent=None, separators=(',', ':'))
        
        # Validate it can be parsed back
        parsed_data = json.loads(json_str)
        
        return cleaned_data, True
    except Exception as e:
        print(f"JSON validation failed: {str(e)}")
        # Return a safe fallback structure
        safe_fallback = {
            "error": "Data serialization failed",
            "error_details": safe_serialize_value(str(e)),
            "original_data_type": safe_serialize_value(str(type(data)))
        }
        return safe_fallback, False

# Pydantic models for request/response
class JobDescriptionRequest(BaseModel):
    job_desc: str
    job_id: Optional[str] = None

class CandidateResponse(BaseModel):
    name: str
    linkedin_url: Optional[str] = None
    fit_score: float
    score_breakdown: Dict[str, float]
    outreach_message: Optional[str] = None
    
    @validator('outreach_message', 'name', pre=True)
    def sanitize_text_fields(cls, v):
        if isinstance(v, str):
            return deep_clean_text(v)
        return v

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

class SimpleJobRequest(BaseModel):
    job_desc: str
    job_id: Optional[str] = None
    
    @validator('job_desc', pre=True)
    def clean_job_desc(cls, v):
        if isinstance(v, str):
            return deep_clean_text(v)
        return v

class SimpleJobResponse(BaseModel):
    success: bool
    job_id: Optional[str] = None
    data: Dict[str, Any]
    message: str

# Startup/shutdown context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing database...")
    try:
        create_tables()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Database initialization failed: {e}")
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
        print("Creating new graph instance...")
        _graph = create_graph()
        print("Graph created successfully")
    return _graph

def get_db():
    """Database dependency"""
    with get_db_session() as db:
        yield db

# Background task to process job description
async def process_job_description(job_desc: str, job_id: str = None):
    """Process job description in the background"""
    try:
        # Clean the input first
        clean_job_desc = deep_clean_text(job_desc)
        
        graph = get_graph()
        
        # Initialize state
        initial_state = {
            "job_desc": clean_job_desc,
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
        
        # Clean the result immediately after getting it
        cleaned_result, is_valid = validate_json_response(result)
        
        if not is_valid:
            print("Warning: Result required extensive cleaning for JSON serialization")
        
        return cleaned_result
        
    except Exception as e:
        print(f"Error processing job description: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
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
        cleaned_stats, _ = validate_json_response(stats)
        return {
            "status": "healthy",
            "database": "connected",
            "api_version": "1.0.0",
            "stats": cleaned_stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": safe_serialize_value(str(e))
        }

def preprocess_graph_output(result):
    """Specifically preprocess the graph output to handle known problematic data"""
    if not isinstance(result, dict):
        return result
    
    # Handle specific keys that are known to have issues
    processed_result = {}
    
    for key, value in result.items():
        if key == 'profile_data' and isinstance(value, list):
            # Clean each profile data string
            processed_result[key] = [deep_clean_text(profile) if isinstance(profile, str) else profile for profile in value]
        elif key == 'best_candidate_profile' and isinstance(value, str):
            # Clean the best candidate profile
            processed_result[key] = deep_clean_text(value)
        elif key == 'outreach_message' and isinstance(value, str):
            # Clean the outreach message
            processed_result[key] = deep_clean_text(value)
        elif key == 'jd_info' and value is not None:
            # Handle JDInfo object
            processed_result[key] = safe_serialize_value(value)
        else:
            # Use regular deep serialization for other values
            processed_result[key] = deep_safe_serialize(value, max_depth=5)
    
    return processed_result

@app.post("/analyze-job-simple", summary="Simple Job Analysis")
async def analyze_job_simple(request: SimpleJobRequest):
    """
    Simple job analysis endpoint that returns raw node outputs.
    Takes a job description and returns all processing results as JSON.
    """
    try:
        print(f"Starting job analysis for request: {request.job_desc[:100]}...")
        
        # Clean the input job description
        clean_job_desc = deep_clean_text(request.job_desc)
        print(f"Cleaned job description length: {len(clean_job_desc)}")
        
        graph = get_graph()
        
        # Initialize state with the cleaned job description
        initial_state = {
            "job_desc": clean_job_desc,
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
        
        # Run the graph and get results
        print("Invoking graph...")
        raw_result = graph.invoke(initial_state)
        print("Graph execution completed")
        
        # Preprocess the graph output to handle known issues
        print("Preprocessing graph output...")
        preprocessed_result = preprocess_graph_output(raw_result)
        
        # Clean and validate the result thoroughly
        print("Cleaning and validating result...")
        cleaned_result, is_valid = validate_json_response(preprocessed_result)
        
        if not is_valid:
            print("Warning: Result required fallback serialization")
        
        # Get job_id from result if available
        job_id = request.job_id or safe_serialize_value(cleaned_result.get('job_id', 'unknown'))
        
        # Create the response structure
        response_data = {
            "success": True,
            "job_id": job_id,
            "message": "Job analysis completed successfully",
            "data": cleaned_result
        }
        
        # Final validation of the complete response
        print("Final response validation...")
        final_response, final_valid = validate_json_response(response_data)
        
        if not final_valid:
            print("Warning: Final response required fallback serialization")
        
        print("Returning response successfully")
        return final_response
        
    except Exception as e:
        # Get detailed error information
        error_details = traceback.format_exc()
        print(f"Error in analyze_job_simple: {error_details}")
        
        # Create a safe error response
        error_response = {
            "success": False,
            "job_id": safe_serialize_value(getattr(request, 'job_id', 'unknown')),
            "message": f"Job analysis failed: {safe_serialize_value(str(e))}",
            "data": {
                "error": safe_serialize_value(str(e)),
                "error_type": safe_serialize_value(type(e).__name__),
                "traceback": [safe_serialize_value(line) for line in error_details.split('\n')[-10:]]
            }
        }
        
        # Validate the error response too
        final_error_response, _ = validate_json_response(error_response)
        
        # Return as HTTPException to ensure proper error status
        raise HTTPException(status_code=500, detail=final_error_response)

# Additional helper endpoint for debugging
@app.post("/debug-text-clean", summary="Debug Text Cleaning")
async def debug_text_clean(text: str):
    """Debug endpoint to test text cleaning functionality"""
    try:
        original_length = len(text)
        cleaned_text = deep_clean_text(text)
        cleaned_length = len(cleaned_text)
        
        # Try to serialize to test
        test_obj = {"original": text, "cleaned": cleaned_text}
        serialized, is_valid = validate_json_response(test_obj)
        
        return {
            "original_length": original_length,
            "cleaned_length": cleaned_length,
            "characters_removed": original_length - cleaned_length,
            "is_json_safe": is_valid,
            "cleaned_text": cleaned_text[:500] + "..." if len(cleaned_text) > 500 else cleaned_text
        }
    except Exception as e:
        return {
            "error": safe_serialize_value(str(e)),
            "original_text_preview": safe_serialize_value(text[:100])
        }

@app.get("/api/jobs/{job_id}", response_model=JobWithCandidatesResponse, summary="Get Job with Candidates")
async def get_job_with_candidates(job_id: int):
    """Get a specific job description with all its candidates"""
    try:
        job_data = DatabaseQueryUtils.get_job_with_candidates(job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Clean the job data before returning
        cleaned_data = clean_json_response(job_data)
        return JobWithCandidatesResponse(**cleaned_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job: {str(e)}")

@app.get("/api/best-candidates", response_model=BestCandidatesResponse, summary="Get All Best Candidates")
async def get_best_candidates():
    """Get summary of all best candidates across all jobs"""
    try:
        candidates = DatabaseQueryUtils.get_best_candidates_summary()
        cleaned_candidates = clean_json_response(candidates)
        return BestCandidatesResponse(candidates=cleaned_candidates)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching best candidates: {str(e)}")

@app.get("/api/jobs", summary="Get All Jobs")
async def get_all_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all job descriptions with pagination"""
    try:
        jobs = JobDescriptionCRUD.get_all_job_descriptions(db, skip=skip, limit=limit)
        job_list = [
            {
                "id": job.id,
                "job_title": sanitize_text_for_json(job.job_title) if job.job_title else None,
                "company_name": sanitize_text_for_json(job.company_name) if job.company_name else None,
                "location": sanitize_text_for_json(job.job_location) if job.job_location else None,
                "work_arrangement": sanitize_text_for_json(job.work_arrangement) if job.work_arrangement else None,
                "employment_type": sanitize_text_for_json(job.employment_type) if job.employment_type else None,
                "created_at": job.created_at.isoformat() if job.created_at else None
            }
            for job in jobs
        ]
        return clean_json_response(job_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")

@app.get("/api/candidates/job/{job_id}", summary="Get Candidates by Job ID")
async def get_candidates_by_job(job_id: int, db: Session = Depends(get_db)):
    """Get all candidates for a specific job"""
    try:
        candidates = LinkedInCandidateCRUD.get_candidates_by_job(db, job_id)
        candidate_list = [
            {
                "id": candidate.id,
                "linkedin_url": sanitize_text_for_json(candidate.linkedin_url) if candidate.linkedin_url else None,
                "candidate_name": sanitize_text_for_json(candidate.candidate_name) if candidate.candidate_name else None,
                "current_position": sanitize_text_for_json(candidate.current_position) if candidate.current_position else None,
                "current_company": sanitize_text_for_json(candidate.current_company) if candidate.current_company else None,
                "final_score": candidate.final_score,
                "is_best_candidate": candidate.is_best_candidate,
                "created_at": candidate.created_at.isoformat() if candidate.created_at else None
            }
            for candidate in candidates
        ]
        return clean_json_response(candidate_list)
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
        
        return clean_json_response({
            "message": f"Job {job_id} and all associated candidates deleted successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)