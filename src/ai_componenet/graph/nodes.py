import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import re
import logging
from typing import Dict
from langgraph.graph import StateGraph, START, END
from src.ai_componenet.graph.state import AgentState
from src.ai_componenet.get_llm import get_structured_llm, get_llm
from src.ai_componenet.graph.utils.jdinfo import JDInfo
from src.ai_componenet.graph.utils.models import ScoringOutput, OutreachOutput
from src.ai_componenet.core.prompts import jd_template, scoring_template, outreach_template
from src.ai_componenet.graph.utils.tools import tavily_tool, data_of_linkedin_url
from src.ai_componenet.exception import CustomException
from langchain_core.prompts import PromptTemplate
from typing import Dict, Any

from src.ai_componenet.database.database import get_db_session, create_tables
from src.ai_componenet.database.crud import JobDescriptionCRUD, LinkedInCandidateCRUD

logger = logging.getLogger(__name__)

# Ensure tables are created
create_tables()


def JobDescriptionNode(state: AgentState) -> Dict[str, Any]:
    """Get the job description and store the important information data from that"""
    try:
        logger.info("Enter JobDescriptionNode ------------> ")
        prompt = PromptTemplate(
            template=jd_template,
            input_variables=["job_description"]
        )
        
        llm = get_structured_llm(prompt, JDInfo, model_name="gemini-1.5-flash")
        response = llm.invoke({"job_description": state["job_desc"]})
        
        # Store in database
        with get_db_session() as db:
            db_job = JobDescriptionCRUD.create_job_description(
                db=db,
                jd_info=response,
                original_desc=state["job_desc"]
            )
            job_id = db_job.id
            logger.info(f"Job description stored in database with ID: {job_id}")
        
        return {
            "jd_info": response,
            "job_id": job_id 
        }
    except Exception as e:
        logger.error(f"Error Occurred at JobDescriptionNode : {str(e)}")
        raise CustomException(e, sys) from e 


def LinkedInProfileNode(state: AgentState) -> Dict[str, Any]:
    """Get the linkedin profile of the user on the basis of the JD"""
    try:
        logger.info("Enter LinkedInProfileNode  ----------> ")
        job_title = "software engineer"  # default fallback
        
        if state.get("jd_info") and state["jd_info"].job_title:
            job_title = state["jd_info"].job_title
        
        urls, count = tavily_tool(job_title)
        
        return {
            "linkedin_profile": urls,
            "profile_found": count
        }
    except Exception as e:
        logger.error(f"Error Occurred at LinkedInProfileNode : {str(e)}")
        raise CustomException(e, sys) from e 
        

def FetchURLNode(state: AgentState) -> Dict[str, Any]:
    """Get the user data using LinkedIn URLs"""
    try:
        logger.info("Enter FetchURLNode ------> ")
        urls = state.get("linkedin_profile", [])
        data = []
        
        if urls:  # Check if urls exist and is not None
            for url in urls:
                if url:  # Check if individual URL is not None/empty
                    result = data_of_linkedin_url(url)
                    if result:  # Only append non-empty results
                        data.append(result)
        
        return {
            "profile_data": data
        }
    except Exception as e:
        logger.error(f"Error Occurred at FetchURLNode : {str(e)}")
        raise CustomException(e, sys) from e 


def ScoringNode(state: AgentState) -> Dict[str, Any]:
    """Score each profile based on their background and JD"""
    try:
        logger.info("Enter ScoringNode --------> ")
        prompt = PromptTemplate(
            template=scoring_template,
            input_variables=["profile_data", "job_desc"]
        )
        
        fit_scores = []
        score_breakdowns = []
        candidate_ids = []  # Store database IDs
        
        # Check if profile_data exists
        if not state.get("profile_data"):
            logger.warning("No profile data found in state")
            return {
                "fit_score": [],
                "score_breakdown": [],
                "candidate_ids": []
            }
        
        job_id = state.get("job_id")
        if not job_id:
            logger.error("No job_id found in state")
            raise CustomException("Job ID not found in state", sys)
    
        for i, data in enumerate(state["profile_data"]):
            try:
                llm = get_structured_llm(prompt, ScoringOutput, model_name="gemini-1.5-flash")
                response = llm.invoke({
                    "profile_data": data, 
                    "job_desc": state["job_desc"]
                })
                
                fit_scores.append(response.final_score)
                score_breakdowns.append(response.score_breakdown)
                
                # Store candidate data in database
                with get_db_session() as db:
                    linkedin_url = state["linkedin_profile"][i] if i < len(state["linkedin_profile"]) else None
                    
                    db_candidate = LinkedInCandidateCRUD.create_candidate(
                        db=db,
                        job_description_id=job_id,
                        profile_data=data,
                        linkedin_url=linkedin_url,
                        final_score=response.final_score,
                        score_breakdown=response.score_breakdown
                    )
                    candidate_ids.append(db_candidate.id)
                    logger.info(f"Candidate {i+1} stored in database with ID: {db_candidate.id}")
            
            except Exception as e:
                logger.error(f"Error scoring profile {i}: {str(e)}")
                # Provide default scores if scoring fails
                default_breakdown = {
                    "Education": 6.0,
                    "Career_Trajectory": 6.0, 
                    "Company_Relevance": 6.0,
                    "Experience_Match": 6.0,
                    "Location_Match": 6.0,
                    "Tenure": 6.0
                }
                fit_scores.append(6.0)
                score_breakdowns.append(default_breakdown)
                
                # Store failed candidate with default scores
                with get_db_session() as db:
                    linkedin_url = state["linkedin_profile"][i] if i < len(state["linkedin_profile"]) else None
                    
                    db_candidate = LinkedInCandidateCRUD.create_candidate(
                        db=db,
                        job_description_id=job_id,
                        profile_data=data,
                        linkedin_url=linkedin_url,
                        final_score=6.0,
                        score_breakdown=default_breakdown
                    )
                    candidate_ids.append(db_candidate.id)

        return {
            "fit_score": fit_scores,
            "score_breakdown": score_breakdowns,
            "candidate_ids": candidate_ids
        }
    except Exception as e:
        logger.error(f"Error Occurred at ScoringNode : {str(e)}")
        raise CustomException(e, sys) from e 

def BestCandidateNode(state: AgentState) -> Dict[str, Any]:
    """
    Find the best candidate with highest score and generate outreach message
    """
    try:
        logger.info("Enter BestCandidateNode  ---------> ")
        # Validate required data exists
        if not state.get("fit_score") or not state.get("profile_data"):
            logger.error("Missing fit_score or profile_data in state")
            return {
                "best_candidate_profile": None,
                "best_candidate_score": None,
                "best_candidate_breakdown": None,
                "outreach_message": "Error: No candidate data available"
            }
        
        if not state.get("score_breakdown"):
            logger.error("Missing score_breakdown in state")
            return {
                "best_candidate_profile": None,
                "best_candidate_score": None,
                "best_candidate_breakdown": None,
                "outreach_message": "Error: No score breakdown available"
            }
        
        # Find the index of the candidate with the highest score
        fit_scores = state["fit_score"]
        best_index = fit_scores.index(max(fit_scores))
        
        # Extract best candidate data
        best_candidate_profile = state["profile_data"][best_index]
        best_candidate_score = fit_scores[best_index]
        best_candidate_breakdown = state["score_breakdown"][best_index]
        
        logger.info(f"Best candidate found at index {best_index} with score {best_candidate_score}")
        
        # Generate outreach message
        logger.info("Enter generate_outreach_message function ----> ")
        outreach_message = generate_outreach_message(
            candidate_profile=best_candidate_profile,
            job_desc=state["job_desc"],
            candidate_score=best_candidate_score,
            score_breakdown=best_candidate_breakdown
        )
        
        # Update the best candidate in database
        if state.get("candidate_ids") and len(state["candidate_ids"]) > best_index:
            best_candidate_id = state["candidate_ids"][best_index]
            with get_db_session() as db:
                LinkedInCandidateCRUD.update_best_candidate(
                    db=db,
                    candidate_id=best_candidate_id,
                    outreach_message=outreach_message
                )
                logger.info(f"Updated best candidate in database with ID: {best_candidate_id}")
        
        return {
            "best_candidate_profile": best_candidate_profile,
            "best_candidate_score": best_candidate_score,
            "best_candidate_breakdown": best_candidate_breakdown,
            "outreach_message": outreach_message
        }
            
    except Exception as e:
        logger.error(f"Error Occurred at BestCandidateNode : {str(e)}")
        raise CustomException(e, sys) from e 


def sanitize_outreach_message(message: str) -> str:
    """
    Sanitize outreach message to prevent JSON parsing issues.
    """
    if not message:
        return ""
    
    # Remove excessive whitespace and normalize line endings
    message = re.sub(r'\r\n|\r', '\n', message)
    message = re.sub(r'\n{3,}', '\n\n', message)  # Limit consecutive newlines
    message = re.sub(r'[ \t]+', ' ', message)     # Normalize spaces
    
    # Remove control characters except newlines and basic formatting
    message = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', message)
    
    # Ensure proper escaping for JSON
    message = message.replace('\\', '\\\\')
    message = message.replace('"', '\\"')
    
    return message.strip()

def generate_outreach_message(candidate_profile: str, job_desc: str, 
                            candidate_score: float, score_breakdown: Dict[str, float]) -> str:
    """Generate personalized outreach message for the best candidate"""
    
    try:
        prompt = PromptTemplate(
            template=outreach_template,
            input_variables=["candidate_profile", "job_desc", "candidate_score", "score_breakdown"]
        )
        
        # Format score breakdown for readability
        breakdown_text = "\n".join([f"- {k.replace('_', ' ')}: {v}/10" for k, v in score_breakdown.items()])
        
        llm = get_llm(prompt, model_name="gemini-1.5-flash")
        response = llm.invoke(
            {
                "candidate_profile": candidate_profile,
                "job_desc": job_desc,
                "candidate_score": candidate_score,
                "score_breakdown": score_breakdown
            }
        )
        
        if hasattr(response, 'content'):
            outreach_message = response.content
        else:
            outreach_message = str(response)
        
        # Sanitize the message before returning
        outreach_message = sanitize_outreach_message(outreach_message)
        
        logger.info("Outreach message successfully created and sanitized")
        return outreach_message
        
    except Exception as e:
        logger.error(f"Error Occurred at generate_outreach_message function : {str(e)}")
        # Return a safe fallback message
        return "Thank you for your interest in our position. We would like to discuss this opportunity with you further."