from typing import List
from persons.asynchronous_persons.fine_tuned_asynchronous_person import FineTunedAsynchronousPerson
from persons.asynchronous_persons.hugging_face_model import HuggingFaceModel
from session_rooms.session_room import ChatEntry
import logging

log = logging.getLogger(__name__)

PASS_TURN_TOKEN = "<pass>"


class FineTunedMafiaPlayer(FineTunedAsynchronousPerson):

    def __init__(self, model_path: str, background_story: str, name: str,
                 pass_turn_token: str = PASS_TURN_TOKEN, **model_kwargs):
        super().__init__(HuggingFaceModel(local_model_path=model_path, **model_kwargs),
                         background_story, name)
        self.pass_turn_token = pass_turn_token

    def create_prompt(self, experiment_scenario_not_used, chat_list: List[ChatEntry]) -> str:
        prompt = ""
        if chat_list:
            prompt += chat_list[-1].prompt + chat_list[-1].answer.strip() + " "
        return prompt + f"<player name> {self.name} <text> "

    def should_generate_answer(self, potential_answer: str) -> bool:
        """
        :return: whether to return the potential generated answer, based on the pre-defined rules
        (such as skipping certain possible outputs)
        """
        return bool(potential_answer.strip()) and \
            (self.generation_model.generate_without_special_tokens
             or self.pass_turn_token not in potential_answer)
