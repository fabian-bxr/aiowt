from pydantic import BaseModel
from typing import List, Literal, Optional


class Objective(BaseModel):
    primary: bool
    status: Literal["in_progress", "completed", "failed"]
    text: str


class Mission(BaseModel):
    objectives: Optional[List[Objective]]
    status: Literal["running", "fail"]
