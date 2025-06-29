import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import os
import base64
import re
import json
import requests
import logging
from io import BytesIO
from typing import List
from PyPDF2 import PdfReader
from langchain_tavily import TavilySearch
from src.ai_componenet.logger import logging
from src.ai_componenet.exception import CustomException
from dotenv import load_dotenv
load_dotenv()


logger = logging.getLogger(__name__)

tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    raise ValueError("TAVILY_API_KEY environment variable is not set")

os.environ["TAVILY_API_KEY"] = tavily_api_key


rapid_api_key = os.getenv("RAPID_API_KEY")
if not rapid_api_key:
    raise ValueError("RAPID_API_KEY environment variable is not set")



def tavily_tool(job_position: str, max_result: int = 5) -> List[str]:
    """Search top Job seekers on linkedin according to job description and get the LinkedIn URLs

    Args:
        job_position (str): Search for the given job position
        max_result (int): Maximum number of results to return (default: 5)
    
    Returns:
        List[str]: List of LinkedIn profile URLs
    """
    try:
        logger.info("Enter Tavily tool ----> ")
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
        logger.info("tavily tool Executed completed successfully   <------------")
        
        return urls
    
    except CustomException as e:
        print(f"Error in tavily_tool: {e}")
        return []  # Return empty list on error rather than crashing



def data_of_linkedin_url(linkedin_url: str) -> str:
    """Get the User data using LinkedIn URL
    
    Args:
        linkedin_url (str): URL to fetch data
    
    Returns:
        str: Extracted text data from the LinkedIn profile PDF
    """
    try:
        logger.info("Enter data_of_linkedin_url tool -----------> ")
        url = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-profile-pdf-cv"
        querystring = {"linkedin_url": linkedin_url}
        headers = {
            "x-rapidapi-key": rapid_api_key,
            "x-rapidapi-host": "fresh-linkedin-profile-data.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json().get("data", {})
        
        # Extract the base64 string
        b64 = data.get("base64encoded_pdf", "")
        if not b64:
            print(f"No PDF data found for URL: {linkedin_url}")
            return ""
        
        # Handle base64 data with or without data URI prefix
        match = re.match(r"data:application/pdf;base64,(.*)", b64)
        pdf_b64 = match.group(1) if match else b64
        
        # Decode and load into BytesIO
        pdf_bytes = base64.b64decode(pdf_b64)
        pdf_file = BytesIO(pdf_bytes)
        
        # Using PDF reader to extract text
        reader = PdfReader(pdf_file)
        full_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
        
        text = "\n".join(full_text)
        logger.info("data_of_linkedin_url successfully executed successfully")
        return text
        
    except requests.RequestException as e:
        print(f"Request error for URL {linkedin_url}: {e}")
        return ""
    except CustomException as e:
        print(f"Error processing URL {linkedin_url}: {e}")
        return ""