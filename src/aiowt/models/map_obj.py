from pydantic import BaseModel, Field, RootModel, model_validator
from typing import List, Optional, Literal, Iterator


class MapObject(BaseModel):
    type: str
    color: str
    color_array: List[int] = Field(alias="color[]")
    blink: int
    icon: str
    icon_bg: str
    x: Optional[float] = None
    y: Optional[float] = None
    sx: Optional[float] = None
    sy: Optional[float] = None
    ex: Optional[float] = None
    ey: Optional[float] = None
    dx: Optional[float] = None
    dy: Optional[float] = None
    team: Optional[Literal["friendly", "enemy"]] = None

    @model_validator(mode='after')
    def set_team(self):
        if self.color in ['#fa0C00', '#f00C00']:
            self.team = 'enemy'
        else:
            self.team = 'friendly'
        return self


class MapObj(RootModel[List[MapObject]]):
    root: List[MapObject]

    def __getitem__(self, item) -> MapObject:
        return self.root[item]

    def __iter__(self) -> Iterator[MapObject]:
        return iter(self.root)

    def __len__(self):
        return len(self.root)

    def enemies(self) -> "MapObj":
        return MapObj(root=[obj for obj in self.root if obj.team == "enemy"])

    def friendlies(self) -> "MapObj":
        return MapObj(root=[obj for obj in self.root if obj.team == "friendly"])

    def player(self) -> Optional[MapObject]:
        return next((obj for obj in self.root if obj.icon == 'Player'), None)
