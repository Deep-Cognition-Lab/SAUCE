from typing import List, Union

from persons.human import Human
from persons.asynchronous_persons.asynchronous_person import AsynchronousPerson
from session_rooms.ChatEntry import ChatEntry


class AsynchronousHuman(Human, AsynchronousPerson):
    PERSON_TYPE = "asynchronous_human"

    def should_generate_answer(self, unused_context) -> bool:
        """
        :param unused_context: chat history, prompt, scenario, etc.
        :return: whether to currently generate an answer.
        """
        user_want_to_answer = input("Would you like to add an answer? [Y/N] ")
        return user_want_to_answer in ["Y", "y", "yes", "Yes", "YES"]

    def generate_answer(self, experiment_scenario: str, chat_list: List[ChatEntry]) -> Union[ChatEntry, None]:
        if self.should_generate_answer(experiment_scenario):
            return super().generate_answer(experiment_scenario, chat_list)
        else:
            return None
