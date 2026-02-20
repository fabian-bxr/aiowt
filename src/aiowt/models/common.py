from pydantic import BaseModel
from typing import Literal

class InvalidState(BaseModel):
    valid: Literal[False] = False