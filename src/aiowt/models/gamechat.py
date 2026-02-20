from pydantic import BaseModel, RootModel
from typing import List, Iterator


class Message(BaseModel):
    id: int
    msg: str
    sender: str
    enemy: bool
    mode: str


class GameChat(RootModel[List[Message]]):
    root: List[Message]

    def __getitem__(self, item) -> Message:
        return self.root[item]

    def __iter__(self) -> Iterator[Message]:
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)
