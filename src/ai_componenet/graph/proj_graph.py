import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from functools import lru_cache
from langgraph.graph import END, START, StateGraph
from src.ai_componenet.graph.nodes import JobDescriptionNode, LinkedInProfileNode, FetchURLNode, ScoringNode, BestCandidateNode
from src.ai_componenet.graph.state import AgentState
from src.ai_componenet.database.database import create_tables
from src.ai_componenet.database.utils import DatabaseQueryUtils


def create_graph():
    """Create and compile the LangGraph workflow"""
    
    # Ensure database tables exist
    create_tables()
    
    # Create the state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("job_description", JobDescriptionNode)
    workflow.add_node("linkedin_profile", LinkedInProfileNode)
    workflow.add_node("fetch_url", FetchURLNode)
    workflow.add_node("scoring_user", ScoringNode)
    workflow.add_node("best_candidate", BestCandidateNode)
    
    # Add edges to define the flow
    workflow.add_edge(START, "job_description")
    workflow.add_edge("job_description", "linkedin_profile")
    workflow.add_edge("linkedin_profile", "fetch_url")
    workflow.add_edge("fetch_url", "scoring_user")
    workflow.add_edge("scoring_user", "best_candidate")
    workflow.add_edge("best_candidate", END)
    
    # Compile the graph
    return workflow.compile()


# Example usage and testing
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
        "job_id": None,
        "linkedin_profile": None,
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
    
    # Display results
    print("="*50)
    print("JOB DESCRIPTION:")
    print("="*50)
    print(result["job_desc"])
    
    print("\n" + "="*50)
    print("PARSED JD INFO:")
    print("="*50)
    print(result["jd_info"])
    
    print("\n" + "="*50)
    print("LINKEDIN PROFILES FOUND:")
    print("="*50)
    print(result["linkedin_profile"])
    
    print("\n" + "="*50)
    print("CANDIDATE SCORES:")
    print("="*50)
    for i, score in enumerate(result["fit_score"]):
        print(f"Candidate {i+1}: {score}/10")
    
    print("\n" + "="*50)
    print("BEST CANDIDATE:")
    print("="*50)
    print(f"Score: {result['best_candidate_score']}/10")
    print(f"Breakdown: {result['best_candidate_breakdown']}")
    
    print("\n" + "="*50)
    print("OUTREACH MESSAGE:")
    print("="*50)
    print(result["outreach_message"])
    
    # Database queries examples
    if result.get("job_id"):
        print("\n" + "="*50)
        print("DATABASE QUERY RESULTS:")
        print("="*50)
        
        # Get job with candidates from database
        job_data = DatabaseQueryUtils.get_job_with_candidates(result["job_id"])
        if job_data:
            print(f"Job Title: {job_data['job']['job_title']}")
            print(f"Company: {job_data['job']['company_name']}")
            print(f"Total Candidates: {len(job_data['candidates'])}")
            
            # Show best candidate from database
            best_candidates = [c for c in job_data['candidates'] if c['is_best_candidate'] == 'Yes']
            if best_candidates:
                best = best_candidates[0]
                print(f"Best Candidate Score: {best['final_score']}/10")
                print(f"LinkedIn URL: {best['linkedin_url']}")
        
        # Get statistics
        stats = DatabaseQueryUtils.get_job_statistics()
        print(f"\nDatabase Statistics:")
        print(f"Total Jobs: {stats['total_jobs']}")
        print(f"Total Candidates: {stats['total_candidates']}")
        print(f"Best Candidates: {stats['best_candidates']}")
        print(f"Average Score: {stats['average_final_score']}/10")