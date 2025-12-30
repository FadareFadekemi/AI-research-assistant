from pydantic import BaseModel
from typing import List, Optional

class AnalysisPlan(BaseModel):
    descriptives: bool = True
    chi_square: Optional[dict] = None
    cronbach_alpha: Optional[List[str]] = None
    regression: Optional[dict] = None
    ml_model: Optional[str] = None
