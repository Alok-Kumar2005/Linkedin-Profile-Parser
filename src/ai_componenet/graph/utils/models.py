from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Union
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
                # Parse JSON string to dictionary
                return json.loads(v)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract using regex
                import re
                scores = {}
                # Look for patterns like "Education": 7.5
                patterns = re.findall(r'"([^"]+)":\s*(\d+\.?\d*)', v)
                for key, value in patterns:
                    scores[key] = float(value)
                return scores if scores else {}
        elif isinstance(v, dict):
            return v
        else:
            return {}