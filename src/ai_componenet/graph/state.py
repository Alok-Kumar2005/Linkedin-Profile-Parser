from typing import Optional, List, TypedDict, Dict, Union
from src.ai_componenet.graph.utils.jdinfo import JDInfo

class AgentState(TypedDict):
    job_desc: str
    jd_info: Optional[JDInfo]
    job_id: Optional[int] 
    linkedin_profile: Optional[List[str]]
    profile_found: Optional[int]
    profile_data: Optional[List[str]]
    fit_score: Optional[List[float]]
    score_breakdown: Optional[List[Dict[str, float]]]
    candidate_ids: Optional[List[int]] 
    # New fields for best candidate
    best_candidate_profile: Optional[str]
    best_candidate_score: Optional[float]
    best_candidate_breakdown: Optional[Dict[str, float]]
    outreach_message: Optional[str]