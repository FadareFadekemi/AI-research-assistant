from pydantic import BaseModel
from typing import List

class DatasetSchema(BaseModel):
    columns: List[str]
    n_rows: int
    n_columns: int
