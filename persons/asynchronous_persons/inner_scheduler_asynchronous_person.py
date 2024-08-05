from typing import Union, List
from persons.asynchronous_persons.asynchronous_person import AsynchronousPerson
from abc import ABC, abstractmethod
from persons.asynchronous_persons.hugging_face_model import HuggingFaceModel
from session_rooms.session_room import ChatEntry
import logging
from functools import cache

log = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"


# _shared_hugging_face_models = {}
# def get_shared_model(model_name: str) -> HuggingFaceModel:
#     if model_name not in _shared_hugging_face_models:
#         _shared_hugging_face_models[model_name] = init_hugging_face_model(model_name)
#     return _shared_hugging_face_models[model_name]
@cache
def get_shared_model(model_name: str) -> HuggingFaceModel:
    return init_hugging_face_model(model_name)


def init_hugging_face_model(model_name: str, is_pretrained: bool = True) -> HuggingFaceModel:
    """
    Argument `is_pretrained` is currently only used as default, for simplicity reasons.
    If needed, the code can be easily modified to get an "is_pretrained" argument
    for the generation model and/or the inner scheduler model from the initial configuration.
    """
    if is_pretrained:
        return HuggingFaceModel(pretrained_model_name=model_name)
    else:
        return HuggingFaceModel(local_model_path=model_name)


class InnerSchedulerAsynchronousPerson(AsynchronousPerson, ABC):
    def __init__(self, background_story: str, name: str,
                 generation_model_name: str = DEFAULT_MODEL_NAME,
                 inner_scheduler_model_name: str = DEFAULT_MODEL_NAME, *args, **kwargs):
        super().__init__(background_story, name, *args, **kwargs)
        self.is_generation_model_shared = kwargs.get("is_generation_model_shared", True)
        self.is_inner_scheduler_model_shared = kwargs.get("is_inner_scheduler_model_shared", True)
        self.generation_model_name = generation_model_name
        self.inner_scheduler_model_name = inner_scheduler_model_name
        if self.is_generation_model_shared:
            self.generation_model = get_shared_model(self.generation_model_name)
        else:
            self.generation_model = init_hugging_face_model(self.generation_model_name)
        if self.is_inner_scheduler_model_shared:
            self.inner_scheduler_model = get_shared_model(self.inner_scheduler_model_name)
        else:
            self.inner_scheduler_model = init_hugging_face_model(self.inner_scheduler_model_name)

    @abstractmethod
    def create_context_for_scheduler(self, experiment_scenario: str, chat_list: List[ChatEntry]
                                     ) -> str:
        """
        Creates the context (chat history, prompt, scenario, etc.) used by the inner scheduler to
        decide whether to generate an answer.
        """
        raise NotImplementedError()

    @abstractmethod
    def should_generate_answer(self, context: str) -> bool:
        """
        Decides whether to currently generate an answer, based on the context,
        using self.inner_scheduler_model.
        """
        raise NotImplementedError()

    @abstractmethod
    def create_prompt(self, experiment_scenario: str, chat_list: List[ChatEntry]) -> str:
        """Creates the prompt for the generation model,
        once the inner scheduler has decided it should"""
        raise NotImplementedError()

    def generate_answer(self, experiment_scenario: str, chat_list: List[ChatEntry]
                        ) -> Union[ChatEntry, None]:
        context = self.create_context_for_scheduler(experiment_scenario, chat_list)
        if self.should_generate_answer(context):
            prompt = self.create_prompt(experiment_scenario, chat_list)
            answer = self.generation_model.generate(prompt)
            return ChatEntry(entity=self, prompt=prompt, answer=answer)
        else:
            return None
