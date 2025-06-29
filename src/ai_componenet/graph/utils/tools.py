from langchain_tavily import TavilySearch
from typing import List
import os
from dotenv import load_dotenv
load_dotenv()


# Ensure the API key is properly loaded
tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    raise ValueError("TAVILY_API_KEY environment variable is not set")

os.environ["TAVILY_API_KEY"] = tavily_api_key

def tavily_tool(job_position: str, max_result: int = 5) -> List[str]:
    """Search top Job seekers on linkedin according to job description and get the LinkedIn URLs

    Args:
        job_position (str): Search for the given job position
        max_result (int): Maximum number of results to return (default: 5)
    
    Returns:
        List[str]: List of LinkedIn profile URLs
    """
    try:
        tool = TavilySearch(max_results=max_result, topic="general")
        query = (
            f'site:linkedin.com/in '
            f'"{job_position}" '
            f'"Open to work" '
            f'-jobs -company -post'
        )
        result = tool.invoke({"query": query})
        
        urls = []
        if 'results' in result:
            for item in result['results']:
                if 'url' in item:
                    urls.append(item['url'])
        
        return urls
    
    except Exception as e:
        print(f"Error in tavily_tool: {e}")
        return []  # Return empty list on error rather than crashing