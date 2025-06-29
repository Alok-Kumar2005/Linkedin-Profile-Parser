from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Union

class JDInfo(BaseModel):
    job_title: Optional[str] = Field(
        default=None, 
        description="The title of the job position"
    )
    
    company_name: Optional[str] = Field(
        default=None, 
        description="The name of the company"
    )
    
    company_description: Optional[str] = Field(
        default=None, 
        description="Brief description about the company"
    )
    
    job_location: Optional[str] = Field(
        default=None, 
        description="The location where the job is based (city, state, country)"
    )
    
    work_arrangement: Optional[Literal["remote", "hybrid", "onsite", "flexible"]] = Field(
        default=None, 
        description="ONLY the work arrangement type. Use 'onsite' for in-person work, 'remote' for work from home, 'hybrid' for combination, 'flexible' for flexible arrangements. Do NOT include employment type here."
    )
    
    employment_type: Optional[Literal["full-time", "part-time", "contract", "internship", "temporary"]] = Field(
        default=None, 
        description="ONLY the type of employment schedule. Use 'full-time' for full-time positions, 'part-time' for part-time, etc. Do NOT include work arrangement here."
    )
    
    salary_range: Optional[str] = Field(
        default=None, 
        description="The salary range or compensation details if mentioned"
    )
    
    experience_required: Optional[str] = Field(
        default=None, 
        description="Required years of experience or experience level (e.g., '2+ years', 'Senior level', etc.)"
    )
    
    education_requirements: Optional[List[str]] = Field(
        default=None, 
        description="Educational qualifications or degree requirements"
    )
    
    technical_skills: Optional[List[str]] = Field(
        default=None, 
        description="Technical skills and technologies required (programming languages, frameworks, tools, etc.)"
    )
    
    soft_skills: Optional[List[str]] = Field(
        default=None, 
        description="Soft skills and interpersonal abilities required"
    )
    
    key_responsibilities: Optional[List[str]] = Field(
        default=None, 
        description="Primary roles and responsibilities of the position"
    )
    
    job_requirements: Optional[List[str]] = Field(
        default=None, 
        description="Specific requirements and qualifications needed"
    )
    
    preferred_qualifications: Optional[List[str]] = Field(
        default=None, 
        description="Nice-to-have qualifications that are preferred but not mandatory"
    )
    
    tools_technologies: Optional[List[str]] = Field(
        default=None, 
        description="Specific tools, platforms, or technologies mentioned (IDEs, databases, cloud platforms, etc.)"
    )
    
    industry: Optional[str] = Field(
        default=None, 
        description="The industry or sector the company operates in"
    )
    
    seniority_level: Optional[Literal["entry", "junior", "mid", "senior", "lead", "principal", "director"]] = Field(
        default=None, 
        description="The seniority level of the position based on requirements and responsibilities"
    )