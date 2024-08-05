from __future__ import annotations

import random
from typing import List

from hosts.host import Host
# protect cyclic imports caused from typing
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from persons.person import Person


class HostRandom(Host):
    NAME = "random"

    def __init__(self, persons: List[Person], start_person_index: int, *args, **kwargs):
        super().__init__(persons, start_person_index)

    def get_curr_person_and_move_to_next(self) -> Person:
        current_person = self.current_person
        self.current_person = random.choice(self.persons)
        return current_person

