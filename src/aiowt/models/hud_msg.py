from pydantic import BaseModel
from typing import List, Optional


class Damage(BaseModel):
    id: int
    msg: str
    sender: str
    enemy: bool
    mode: str
    time: int


class Event(BaseModel):
    id: int
    msg: str


class HudMsg(BaseModel):
    events: List[Event]
    damage: List[Damage]
