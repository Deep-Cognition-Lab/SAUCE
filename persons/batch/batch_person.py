from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from session_rooms.ChatEntry import BatchChatList, ChatEntry


@dataclasses.dataclass
class InBatchPerson:
    """Pure data class for a person."""
    background_story: str
    name: str
    # Special tag to identify the person.
    tag: str


class BatchedPerson(ABC):
    """
    Represents a batch of persons, each with its own name and description.
    This class is used to run multiple persons in parallel.
    """
    PERSON_TYPE = None

    def __init__(self,
                 background_stories: list[str],
                 names: list[str],
                 tag: str,
                 *args, **kwargs):
        self.persons = [InBatchPerson(story, name, tag) for story, name in zip(background_stories, names)]
        self.background_stories = background_stories
        self.names = names
        self.tag = tag
        if len(background_stories) != len(names):
            raise ValueError("Each batch person must have the same number of stories and names")

    @property
    def batch_count(self) -> int:
        return len(self.background_stories)

    @abstractmethod
    def generate_answer(
            self, experiment_scenario: str, chat_lists: BatchChatList,*args,**kwargs) -> list[ChatEntry]:
        """
        Receives the current session state and returns the next ChatEntry for each
        of the chat lists in `chat_lists`.
        """
        raise NotImplementedError()
