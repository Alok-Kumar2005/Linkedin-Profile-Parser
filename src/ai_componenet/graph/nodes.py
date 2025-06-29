import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from langgraph.graph import StateGraph, START, END
from src.ai_componenet.graph.state import AgentState
from src.ai_componenet.get_llm import get_structured_llm, get_llm
from src.ai_componenet.graph.utils.jdinfo import JDInfo
from src.ai_componenet.core.prompts import jd_template
from src.ai_componenet.graph.utils.tools import tavily_tool, data_of_linkedin_url
from langchain_core.prompts import PromptTemplate
from typing import Dict, Any


def JobDescriptionNode(state: AgentState) -> Dict[str, Any]:
    """Get the job description and store the important information data from that"""
    prompt = PromptTemplate(
        template=jd_template,
        input_variables=["job_description"]
    )
    
    llm = get_structured_llm(prompt, JDInfo, model_name="gemini-1.5-flash")
    response = llm.invoke({"job_description": state["job_desc"]})
    
    return {
        "jd_info": response
    }


def LinkedInProfileNode(state: AgentState) -> Dict[str, Any]:
    """Get the linkedin profile of the user on the basis of the JD"""
    job_title = "software engineer"  # default fallback
    
    if state.get("jd_info") and state["jd_info"].job_title:
        job_title = state["jd_info"].job_title
    
    urls = tavily_tool(job_title)
    
    return {
        "linkedin_profile": urls
    }


def FetchURLNode(state: AgentState) -> Dict[str, Any]:
    """Get the user data using LinkedIn URLs"""
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