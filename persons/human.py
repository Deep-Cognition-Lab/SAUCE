from typing import List, Union

from persons.person import Person
from session_rooms.ChatEntry import ChatEntry


class Human(Person):
    PERSON_TYPE = "human"

    def __init__(self, background_story: str = None, name: str = None, *args, **kwargs):
        super().__init__(background_story, name, *args, **kwargs)
        if not name:
            self.name = input("Please insert your name: ")

    def generate_answer(self, experiment_scenario: str, chat_list: List[ChatEntry]) -> Union[ChatEntry, None]:
        prompt = f"The experiment scenario is: {experiment_scenario}"
        if self.background_story:
            prompt += "\n" + "Don't forget you backstory: " + self.background_story
        prompt += "\n" + "Please insert your answer:\n"
        answer = input(prompt)
        return ChatEntry(entity=self, answer=answer, prompt=prompt)
