import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from langgraph.graph import StateGraph, START, END
from src.ai_componenet.graph.state import AgentState
from src.ai_componenet.get_llm import get_structured_llm, get_llm
from src.ai_componenet.graph.utils.jdinfo import JDInfo
from src.ai_componenet.core.prompts import jd_template
from src.ai_componenet.graph.utils.tools import tavily_tool
from langchain_core.prompts import PromptTemplate


def JobDescriptionNode(state: AgentState) -> AgentState:
    """Get the job description and store the important information data from that"""
    prompt = PromptTemplate(
        template=jd_template,
        input_variables=["job_description"]
    )
    
    llm = get_structured_llm(prompt, JDInfo, model_name="gemini-1.5-flash")
    response = llm.invoke({"job_description": state.job_desc})
    
    return AgentState(
        job_desc=state.job_desc,
        jd_info=response,
        linkedin_profile=state.linkedin_profile
    )


def LinkedInProfileNode(state: AgentState) -> AgentState:
    """Get the linkedin profile of the user on the basis of the JD"""
    job_title = ""
    if state.jd_info and hasattr(state.jd_info, 'job_title'):
        job_title = state.jd_info.job_title
    elif state.jd_info and hasattr(state.jd_info, 'title'):
        job_title = state.jd_info.title
    else:
        job_title = "software engineer"  # right now going with software engineer
    
    print("="*100)
    print(job_title)
    print("="*100)
    
    urls = tavily_tool(job_title)
    
    return AgentState(
        job_desc=state.job_desc,
        jd_info=state.jd_info,
        linkedin_profile=urls
    )