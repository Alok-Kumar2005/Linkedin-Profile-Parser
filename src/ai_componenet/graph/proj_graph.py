import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from functools import lru_cache
from langgraph.graph import END, START, StateGraph
from src.ai_componenet.graph.nodes import JobDescriptionNode, LinkedInProfileNode, FetchURLNode, ScoringNode
from src.ai_componenet.graph.state import AgentState


def create_graph():
    """Create and compile the LangGraph workflow"""
    
    # Create the state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("job_description", JobDescriptionNode)
    workflow.add_node("linkedin_profile", LinkedInProfileNode)
    workflow.add_node("fetch_url", FetchURLNode)
    workflow.add_node("scoring_user", ScoringNode)
    
    # Add edges to define the flow
    workflow.add_edge(START, "job_description")
    workflow.add_edge("job_description", "linkedin_profile")
    workflow.add_edge("linkedin_profile", "fetch_url")
    workflow.add_edge("fetch_url", "scoring_user")
    workflow.add_edge("scoring_user", END)
    
    # Compile the graph
    return workflow.compile()


# Example usage in your main file
if __name__ == "__main__":
    job_desc = """
    Machine Learning Engineer position at TechCorp.
    We are looking for an experienced ML engineer with Python, TensorFlow, and AWS experience.
    Location: San Francisco, CA
    Full-time remote work available.
    """
    
    graph = create_graph()
    
    # Initialize state with required fields
    initial_state = {
        "job_desc": job_desc,
        "jd_info": None,
        "linkedin_profile": None,
        "profile_data": None
    }
    
    result = graph.invoke(initial_state)
    # print("Final result:", result)
    print("*="*50)
    print(result["job_desc"])
    print("*="*50)
    print(result["jd_info"])
    print("*="*50)
    print(result["linkedin_profile"])
    print("*="*50)
    print(result["profile_data"])
    print("*="*50)
    print(result["fit_score"])
    print("*="*50)
    print(result["score_breakdown"])