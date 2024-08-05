from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from typing import List

# protect cyclic imports caused from typing
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from persons.person import Person
    from persons.batch.batch_person import BatchedPerson
logging.getLogger(__name__).setLevel(logging.DEBUG)


class Host(ABC):
    NAME = None

    def __init__(self, persons: List[Person|BatchedPerson], start_person_index: int = 0, *args, **kwargs):
        self.persons: List[Person|BatchedPerson] = persons
        self.current_person = self.persons[start_person_index]

    @abstractmethod
    def get_curr_person_and_move_to_next(self) -> Person|BatchedPerson:
        raise NotImplementedError("This function not implemented")
