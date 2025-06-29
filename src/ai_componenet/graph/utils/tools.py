from langchain_tavily import TavilySearch
import os


os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

def tavily_tool(job_position: str, max_result: int = 5):
    """ Search top Job seekers on linkedin about according to job description and get the Linkedin URL

    Args:
        job_position: str = Search for the given job
    Return:
        return the list of link of the user
    """
    tool = TavilySearch(max_results = max_result , topic= "general")
    query = (
            'site:linkedin.com/in '
            ' {job_position} '
            '"Open to work" '
            '-jobs -company -post'
        )
    result = tool.invoke({"query": query})
    urls = []
    for item in result['results']:
        urls.append(item['url'])
    # print(urls)
    return urls