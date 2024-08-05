from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TYPE_CHECKING, Union

from termcolor import colored

if TYPE_CHECKING:
    from persons.person import Person
    from session_rooms.session_room import System


@dataclass
class ChatEntry:
    entity: Union['Person', 'System']
    prompt: Any
    answer: str
    # The original embedding from the mind of the agent who generated this entry.
    original_embedding: Any = None
    time: str = None

    def __str__(self):
        name = self.entity.name if hasattr(self.entity,"name") else self.entity.get("name")
        if self.answer.startswith(f"{name}: "):
            without_time = colored(self.answer, 'red')
        else:
            without_time = f"{colored(name, 'red')}: {self.answer}"
        if self.time is not None:
            return f"[{self.time}] {without_time}"
        return without_time

    def __repr__(self):
        return self.__str__()


#region Aliasing
# Represent a single chat room
ChatList = list[ChatEntry]
# Things more efficiently on GPU.
BatchChatList = list[ChatList]
#endregion
