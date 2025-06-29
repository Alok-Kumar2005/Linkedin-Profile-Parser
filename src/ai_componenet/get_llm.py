from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

### Simple LLM model that takes prompt and returns the response
def get_llm(prompt: PromptTemplate, model_name: str = "gemini-1.5-flash"):
    """
    Creates a simple LLM chain that takes a prompt and returns a response.
    
    Args:
        prompt: PromptTemplate object
        model_name: Name of the Google Generative AI model to use
    
    Returns:
        A chain that can be invoked with input variables
    """
    # Initialize the Google Generative AI model
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # Create the chain by combining prompt and model
    chain = prompt | llm
    
    return chain


### LLM model with structured output using pydantic BaseModel
def get_structured_llm(prompt: PromptTemplate, output_schema: BaseModel, model_name: str = "gemini-1.5-flash"):
    """
    Creates an LLM chain that returns structured output based on a Pydantic model.
    
    Args:
        prompt: PromptTemplate object
        output_schema: Pydantic BaseModel class defining the output structure
        model_name: Name of the Google Generative AI model to use
    
    Returns:
        A chain that returns structured output according to the schema
    """
    # Initialize the Google Generative AI model
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # Create structured LLM with output parser
    structured_llm = llm.with_structured_output(output_schema)
    
    # Create the chain
    chain = prompt | structured_llm
    
    return chain


# Example usage and demonstrations
