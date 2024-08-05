from typing import Union, List, TYPE_CHECKING
from persons.asynchronous_persons.asynchronous_person import AsynchronousPerson
from abc import ABC, abstractmethod
from session_rooms.session_room import ChatEntry
import logging
if TYPE_CHECKING:  # meant to protect cyclic imports caused from typing
    from persons.asynchronous_persons.hugging_face_model import HuggingFaceModel

log = logging.getLogger(__name__)


class FineTunedAsynchronousPerson(AsynchronousPerson, ABC):
    def __init__(self, generation_model: HuggingFaceModel, background_story: str, name: str,
                 *args, **kwargs):
        super().__init__(background_story, name, *args, **kwargs)
        self.generation_model = generation_model

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
