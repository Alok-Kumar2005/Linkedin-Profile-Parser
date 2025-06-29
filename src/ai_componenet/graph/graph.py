from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

class Profile(BaseModel):
    job_desc: str