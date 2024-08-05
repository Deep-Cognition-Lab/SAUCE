from __future__ import annotations

from typing import List

from hosts.host import Host
# protect cyclic imports caused from typing
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from persons.person import Person


class HostRoundRobin(Host):
    NAME = "Round Robin Host"

    def __init__(self, persons: List[Person],
                 start_person_index: int,
                 skip: int = 1, *args, **kwargs):
        super().__init__(persons, start_person_index)
        self.current_person_index: int = start_person_index
        self.skip: int = skip

    def get_curr_person_and_move_to_next(self) -> Person:
        current_person = self.current_person
        self.current_person_index = (self.current_person_index + self.skip) % len(self.persons)
        self.current_person = self.persons[self.current_person_index]
        return current_person



