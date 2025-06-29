from typing import Optional, List, TypedDict
from src.ai_componenet.graph.utils.jdinfo import JDInfo


class AgentState(TypedDict):
    job_desc: str
    jd_info: Optional[JDInfo]
    linkedin_profile: Optional[List[str]]
    profile_data: Optional[List[str]]