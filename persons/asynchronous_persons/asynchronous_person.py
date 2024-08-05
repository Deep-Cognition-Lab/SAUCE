from __future__ import annotations
from typing import Union, List, TYPE_CHECKING
from persons.person import Person
from abc import ABC, abstractmethod
import logging
if TYPE_CHECKING:  # meant to protect cyclic imports caused from typing
    from session_rooms.ChatEntry import ChatEntry

log = logging.getLogger(__name__)


class AsynchronousPerson(Person, ABC):
    def __init__(self, background_story: str, name: str, *args, **kwargs):
        super().__init__(background_story, name, *args, **kwargs)

    @abstractmethod
    def should_generate_answer(self, context: Union[str, List[Union[str, ChatEntry]]]) -> bool:
        """
        :param context: chat history, prompt, scenario, etc.
        :return: whether to currently generate an answer.
        """
        raise NotImplementedError()

    @abstractmethod
    def generate_answer(self, experiment_scenario: str, chat_list: List[ChatEntry]
                        ) -> Union[ChatEntry, None]:
        """
        Should be implemented by using the should_generate_answer method to decide whether to return
        a new ChatEntry, or None.
        """
        raise NotImplementedError()
