from typing import Optional, List
from pydantic import BaseModel, model_validator


class AnalyzeRequest(BaseModel):
       message: Optional[str] = None
       url: Optional[str] = None

       @model_validator(mode="after")
       def at_least_one_field(self):
           if not self.message and not self.url:
               raise ValueError("At least one of 'message' or 'url' must be provided.")
           return self

class AnalyzeResponse(BaseModel):
       risk_label: str
       risk_score: int
       flags: List[str]
       ml_label: str
       ml_score: float
       ml_flags: List[str]
       threat_label: str
       threat_score: int
       threat_flags: List[str]
       message_received: Optional[str] = None
       url_received: Optional[str] = None
       note: str
