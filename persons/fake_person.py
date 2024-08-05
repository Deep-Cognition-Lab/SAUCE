""" 
This file contains a Fake Person implementation which can be used for testing.
"""

from persons.person import Person

# protect cyclic imports caused from typing
from typing import TYPE_CHECKING
from session_rooms.ChatEntry import ChatEntry


class FakePerson(Person):
    PERSON_TYPE = "fake_person"

    def __init__(self, name: str, *args, **kwargs):
        super().__init__("unused_background_story", name)
        assert "things_to_say" in kwargs, "You must tell a fake person exactly what to say."
        self.things_to_say = kwargs.get("things_to_say")
        self.things_to_say_idx = 0

    def generate_answer(self, *args,**kwargs):
        if self.things_to_say_idx >= len(self.things_to_say):
            raise IndexError()
        output = self.things_to_say[self.things_to_say_idx]
        self.things_to_say_idx += 1
        return ChatEntry(entity=self, prompt="no_prompt", answer=output)
