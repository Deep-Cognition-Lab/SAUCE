from persons.asynchronous_persons.async_human import AsynchronousHuman
from typing import List, Union
from session_rooms.session_room import ChatEntry
import logging

log = logging.getLogger(__name__)


class AsynchronousHumanMafia(AsynchronousHuman):
    PERSON_TYPE = "async_human_mafia"

    def __init__(self, background_story: str = None, name: str = None, *args, **kwargs):
        super().__init__(background_story, name, *args, **kwargs)
        self.rules_explained = False

    def should_generate_answer(self, experiment_scenario) -> bool:
        """
        :param experiment_scenario: the rules of the game of Mafia, in our case.
        :return: whether to currently generate an answer.
        """
        if not self.rules_explained:
            print(experiment_scenario)
            self.rules_explained = True
        user_want_to_answer = input(f"{self.name}, here's a reminder about your backstory: "
                                    f"{self.background_story}.\n"
                                    f"Would you like to add a message? y/[n]")
        return user_want_to_answer.strip().lower() in ["y", "yes"]

    def generate_answer(self, experiment_scenario: str, chat_list: List[ChatEntry]) -> Union[ChatEntry, None]:
        if self.should_generate_answer(experiment_scenario):
            answer = input(f"Enter your message now - {self.name}: ")
            return ChatEntry(entity=self, answer=answer, prompt=prompt)
        else:
            return None
