"""
This file implant the basic end type based on iterations
"""
from __future__ import annotations

from end_types.end_type import EndType
# protect cyclic imports caused from typing
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from session_rooms.session_room import SessionRoom


class EndTypeNumMsgs(EndType):
    """
    EndType derived class that uses iteration count to decide whether it's finished
    """
    NAME = "iteration"

    def __init__(self, max_num_msgs: int, start_iteration: int = 0, *args, **kwargs):
        """
        Initialize a based iteration finishing flag
        @param max_num_msgs: that will be run
        @param start_iteration: optional starting iteration
        """
        self.max_num_msgs: int = max_num_msgs
        self.current_msg_num: int = start_iteration

    def did_end(self, session_room: SessionRoom) -> bool:

        return session_room.session_length >= self.max_num_msgs

    def __add__(self, other):
        """
        Override the `+` operator
        @param other:
        @return:
        """
        start_iteration = self.current_msg_num
        max_iteration = self.max_num_msgs
        if isinstance(other, int):
            start_iteration += other
        elif isinstance(other, EndTypeNumMsgs):
            start_iteration += other.current_msg_num
            max_iteration += max_iteration
        else:
            raise TypeError(f"Unable to add {type(object)} to {type(self)}")
        return EndTypeNumMsgs(max_iteration, start_iteration)

    def __iadd__(self, other):
        """
        Implements adding to this object for `+=`
        @param other: object to be added
        @return:
        """
        if isinstance(other, int):
            self.current_msg_num += other
        elif isinstance(other, EndTypeNumMsgs):
            self.current_msg_num += other.current_msg_num
            self.max_num_msgs += other.max_num_msgs
        else:
            raise TypeError(f"Unable to add {type(object)} to {type(self)}")

    def __radd__(self, other):
        """
        @param other: object to be added
        @return:
        """
        return self.__add__(other)