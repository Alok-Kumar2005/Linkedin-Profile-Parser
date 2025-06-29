from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from src.ai_componenet.graph.utils.jdinfo import JDInfo

class AgentState(BaseModel):
    job_desc: str
    jd_info: JDInfo