from pydantic import BaseModel
from typing import List, Optional


class Damage(BaseModel):
    id: int
    msg: str
    sender: str
    enemy: bool
    mode: str


class HudMsg(BaseModel):
    events: List[str]
    damage: List[Damage]
