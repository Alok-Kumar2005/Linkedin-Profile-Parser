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
if __name__ == "__main__":
    
    # Example 1: Simple LLM usage
    print("=== Example 1: Simple LLM ===")
    
    # Create a simple prompt template
    simple_prompt = PromptTemplate(
        input_variables=["topic"],
        template="Write a short poem about {topic}."
    )
    
    # Get the LLM chain
    simple_chain = get_llm(simple_prompt)
    
    # Invoke the chain
    try:
        response = simple_chain.invoke({"topic": "artificial intelligence"})
        print("Simple LLM Response:")
        print(response.content)
    except Exception as e:
        print(f"Error with simple LLM: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 2: Structured LLM usage
    print("=== Example 2: Structured LLM ===")
    
    # Define a Pydantic model for structured output
    class PersonInfo(BaseModel):
        name: str
        age: int
        occupation: str
        skills: list[str]
        bio: str
    
    # Create a prompt for structured output
    structured_prompt = PromptTemplate(
        input_variables=["person_description"],
        template="""
        Based on the following description, extract and structure the person's information:
        
        Description: {person_description}
        
        Please provide the information in the requested structured format.
        """
    )
    
    # Get the structured LLM chain
    structured_chain = get_structured_llm(structured_prompt, PersonInfo)
    
    # Test with sample data
    sample_description = """
    John Smith is a 32-year-old software engineer who works at a tech startup. 
    He specializes in Python programming, machine learning, and web development. 
    John has been coding for over 10 years and enjoys solving complex problems 
    and mentoring junior developers.
    """
    
    try:
        structured_response = structured_chain.invoke({"person_description": sample_description})
        print("Structured LLM Response:")
        print(f"Name: {structured_response.name}")
        print(f"Age: {structured_response.age}")
        print(f"Occupation: {structured_response.occupation}")
        print(f"Skills: {', '.join(structured_response.skills)}")
        print(f"Bio: {structured_response.bio}")
    except Exception as e:
        print(f"Error with structured LLM: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 3: More complex structured output
    print("=== Example 3: Complex Structured Output ===")
    
    class MovieReview(BaseModel):
        title: str
        rating: float  # 1-10 scale
        genre: str
        pros: list[str]
        cons: list[str]
        summary: str
        recommended: bool
    
    movie_prompt = PromptTemplate(
        input_variables=["movie_name"],
        template="""
        Write a detailed movie review for "{movie_name}". 
        Provide a rating out of 10, identify the genre, list pros and cons, 
        write a brief summary, and indicate if you'd recommend it.
        """
    )
    
    movie_chain = get_structured_llm(movie_prompt, MovieReview)
    
    try:
        movie_response = movie_chain.invoke({"movie_name": "The Matrix"})
        print("Movie Review (Structured):")
        print(f"Title: {movie_response.title}")
        print(f"Rating: {movie_response.rating}/10")
        print(f"Genre: {movie_response.genre}")
        print(f"Pros: {', '.join(movie_response.pros)}")
        print(f"Cons: {', '.join(movie_response.cons)}")
        print(f"Summary: {movie_response.summary}")
        print(f"Recommended: {'Yes' if movie_response.recommended else 'No'}")
    except Exception as e:
        print(f"Error with movie review: {e}")