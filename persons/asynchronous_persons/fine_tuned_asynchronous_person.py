from typing import Union, List, TYPE_CHECKING
from persons.asynchronous_persons.asynchronous_person import AsynchronousPerson
from persons.asynchronous_persons.hugging_face_model import HuggingFaceModel
from abc import ABC, abstractmethod
from session_rooms.session_room import ChatEntry
import logging

log = logging.getLogger(__name__)


class FineTunedAsynchronousPerson(AsynchronousPerson, ABC):

    def __init__(self, model_path: str, background_story: str, name: str,
                 *args, **kwargs):
        super().__init__(background_story, name, *args, **kwargs)
        self.generation_model = HuggingFaceModel(local_model_path=model_path)

    @abstractmethod
    def create_prompt(self, experiment_scenario: str, chat_list: List[ChatEntry]) -> str:
        raise NotImplementedError()

    @abstractmethod
    def should_generate_answer(self, potential_answer: str) -> bool:
        """
        :return: whether to return the potential generated answer, based on the pre-defined rules
        (such as skipping certain possible outputs)
        """
        raise NotImplementedError()

    def generate_answer(self, experiment_scenario: str, chat_list: List[ChatEntry]
                        ) -> Union[ChatEntry, None]:
        """
        Should be implemented by using the should_generate_answer method to decide whether to return
        a new ChatEntry, or None.
        """
        prompt = self.create_prompt(experiment_scenario, chat_list)
        potential_answer = self.generation_model.generate(prompt)
        if self.should_generate_answer(potential_answer):
            return ChatEntry(entity=self, prompt=prompt, answer=potential_answer)
        else:
            return None
