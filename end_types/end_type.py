"""
Here we describe the abstract EndType class
"""
from __future__ import annotations

from abc import ABC, abstractmethod
# protect cyclic imports caused from typing
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from session_rooms.session_room import SessionRoom


class EndType(ABC):
    """
    The derived class will implement and help the expiration runner
    decide if the experiment is finished
    """
    NAME = None

    def __init__(self,*args,**kwargs):
        pass

    @abstractmethod
    def did_end(self, session_room: SessionRoom) -> bool:
        """
        Should be implanted by derived class, by using the information from experiment, it should decide
        if the experiment is over and return a boolean response
        :param session_room: that is running
        :return: if the experiment is finished
        """
        raise NotImplementedError("This function need to be implemented")