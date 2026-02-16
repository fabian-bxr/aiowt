from pydantic import BaseModel
from typing import List


class MapInfo(BaseModel):
    grid_size: List[float]
    grid_steps: List[float]
    grid_zero: List[float]
    hud_type: int
    map_generation: int
    map_max: List[float]
    map_min: List[float]
    valid: bool
