from __future__ import annotations

import copy
import logging
from abc import ABC, abstractmethod
from typing import Any, Tuple, List, Union

# protect cyclic imports caused from typing
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from session_rooms.ChatEntry import ChatEntry

log = logging.getLogger(__name__)

class Person(ABC):
    PERSON_TYPE = None

    def __init__(self, background_story: str, name: str, *args, **kwargs):
        self.background_story: str = background_story
        self.name: str = name

    @abstractmethod
    def generate_answer(self, experiment_scenario: str, chat_list: List[ChatEntry]
                        ) -> Union[ChatEntry, None]:
        """
        Receives the current session state.
        Returns the ChatEntry to be added to the chat, or None if it currently shouldn't add one
        (when using asynchronous communication).
        """
        raise NotImplementedError()

    def __deepcopy__(self, memodict={}):
        log.debug("We don't allow deep copies of person")
        return copy.copy(self)

    def __json__(self):
        """
        return a json serializable representation of the Person instance for serializing using json.dumps
        """
        return {
            'person_type': self.PERSON_TYPE,
            'background_story': self.background_story,
            'name': self.name
        }
