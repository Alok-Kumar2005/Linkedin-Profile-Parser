from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Union, Optional
import json

class ScoringOutput(BaseModel):
    final_score: float = Field(
        ..., 
        description="Store the final fit_score of the individual as a number between 0-10",
        ge=0,
        le=10
    )
    score_breakdown: Dict[str, float] = Field(
        ..., 
        description="Store the breakdown scores as a dictionary with categories as keys and scores as values"
    )
    
    @field_validator('score_breakdown', mode='before')
    @classmethod
    def parse_score_breakdown(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                import re
                scores = {}
                patterns = re.findall(r'"([^"]+)":\s*(\d+\.?\d*)', v)
                for key, value in patterns:
                    scores[key] = float(value)
                return scores if scores else {}
        elif isinstance(v, dict):
            return v
        else:
            return {}

class OutreachOutput(BaseModel):
    outreach_message: str = Field(
        ..., 
        description="Personalized outreach message for the best candidate"
    )