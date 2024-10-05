from persons.asynchronous_persons.async_human import AsynchronousHuman
from typing import List, Union
from session_rooms.session_room import ChatEntry
from termcolor import colored
import logging

log = logging.getLogger(__name__)


class AsynchronousHumanMafia(AsynchronousHuman):
    PERSON_TYPE = "async_human_mafia"

    def __init__(self, background_story: str = None, name: str = None, role: str = None,
                 *args, **kwargs):
        super().__init__(background_story, name, *args, **kwargs)
        self.role = role if role is not None else "bystander"
        self.rules_explained = False

    def should_generate_answer(self, experiment_scenario) -> bool:
        """
        :param experiment_scenario: the rules of the game of Mafia, in our case.
        :return: whether to currently generate an answer.
        """
        if not self.rules_explained:
            print(colored(experiment_scenario, color="blue"))
            self.rules_explained = True
        user_want_to_answer = input(colored(f"{self.name}, your role is {self.role}"
                                            f"here's a reminder about your backstory: "
                                            f"{self.background_story}.\n"
                                            f"Would you like to add a message? y/[n] ",
                                            color="blue"))
        return user_want_to_answer.strip().lower() in ["y", "yes"]

    def generate_answer(self, experiment_scenario: str, chat_list: List[ChatEntry]) -> Union[ChatEntry, None]:
        if self.should_generate_answer(experiment_scenario):
            prompt = f"Enter your message now - {self.name}: "
            answer = input(colored(prompt, color="blue"))
            return ChatEntry(entity=self, answer=answer, prompt=prompt)
        else:
            return None
