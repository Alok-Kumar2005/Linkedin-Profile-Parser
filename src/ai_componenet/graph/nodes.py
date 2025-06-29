import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from langgraph.graph import StateGraph, START, END
from src.ai_componenet.graph.state import AgentState
from src.ai_componenet.get_llm import get_structured_llm, get_llm
from src.ai_componenet.graph.utils.jdinfo import JDInfo
from langchain_core.prompts import PromptTemplate




def JobDescriptionNode(state: AgentState)-> AgentState:
    """Get the job description and store the important information data from that"""
    prompt = PromptTemplate(
        template="""
        You are a helpful assistant that can extract the important information from the job description.
        """
    )
    llm = get_structured_llm(prompt, JDInfo, model_name="gemini-1.5-flash")
    response = llm.invoke(state.job_desc)
    return {
        "job_desc": state.job_desc,
        "jd_info": response
    }