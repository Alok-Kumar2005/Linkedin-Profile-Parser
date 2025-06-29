import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from functools import lru_cache
from langgraph.graph import END, START, StateGraph
from src.ai_componenet.graph.nodes import JobDescriptionNode
from src.ai_componenet.graph.state import AgentState


@lru_cache
def get_graph():
    graph = StateGraph(AgentState)
    graph.add_node("job_description", JobDescriptionNode)
    graph.add_edge(START, "job_description")
    graph.add_edge("job_description", END)
    return graph


graph = get_graph().compile()

if __name__ == "__main__":
    job_desc = """About the Company:
                Windsurf (formerly Codeium) is a Forbes AI 50 company building the future of developer productivity through AI. With over 200 employees and $243M raised across multiple rounds including a Series C, Windsurf provides cutting-edge in-editor autocomplete, chat assistants, and full IDEs powered by proprietary LLMs. Their user base spans hundreds of thousands of developers worldwide, reflecting strong product-market fit and commercial traction.
                Roles and Responsibilities:
                Train and fine-tune LLMs focused on developer productivity
                Design and prioritize experiments for product impact
                Analyze results, conduct ablation studies, and document findings
                Convert ML discoveries into scalable product features
                Participate in the ML reading group and contribute to knowledge sharing
                Job Requirements:
                2+ years in software engineering with fast promotions
                Strong software engineering and systems thinking skills
                Proven experience training and iterating on large production neural networks
                Strong GPA from a top CS undergrad program (MIT, Stanford, CMU, UIUC, etc.)
                Familiarity with tools like Copilot, ChatGPT, or Windsurf is preferred
                Deep curiosity for the code generation space
                Excellent documentation and experimentation discipline
                Prior experience with applied research (not purely academic publishing)
                Must be able to work in Mountain View, CA full-time onsite
                Excited to build product-facing features from ML research
            """
    result = graph.invoke({"job_desc": job_desc})
    print(result)
    print("="*100)
    print(result.get("jd_info"))
    print("="*100)
    print(result.get("job_desc"))
    print("="*100)