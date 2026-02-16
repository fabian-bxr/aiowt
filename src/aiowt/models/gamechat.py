from pydantic import BaseModel, RootModel
from typing import List


class Message(BaseModel):
    id: int
    msg: str
    sender: str
    enemy: bool
    mode: str


class GameChat(RootModel[List[Message]]):
    root: List[Message]

    def __getitem__(self, item):
        return self.root[item]

    def __iter__(self):
        return iter(self.root)

    def __len__(self):
        return len(self.root)
