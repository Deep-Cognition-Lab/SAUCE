from typing import Union, List
from persons.asynchronous_persons.asynchronous_person import AsynchronousPerson
from abc import ABC, abstractmethod
from persons.asynchronous_persons.hugging_face_model import HuggingFaceModel
from session_rooms.session_room import ChatEntry
import logging
from functools import cache

log = logging.getLogger(__name__)

# DEFAULT_MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"
DEFAULT_MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
# prompts patterns:
INSTRUCTION_INPUT_RESPONSE_PATTERN = "instruction-input-response prompt pattern"
LLAMA3_PATTERN = "Llama 3 pattern"
DEFAULT_PROMPT_PATTERN = "default"



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
        self.prompt_template = self._get_prompt_template(self.generation_model_name)

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

    def _get_prompt_template(self, model_name: str) -> str:
        model_name = model_name.lower()
        if "phi-3" in model_name:
            return INSTRUCTION_INPUT_RESPONSE_PATTERN
        elif "llama-3" in model_name:
            return LLAMA3_PATTERN
        # elif "____" in model_name: return "____"
        else:
            return DEFAULT_PROMPT_PATTERN

    def _create_customized_model_prompt_skeleton(self, **kwargs) -> str:
        if self.prompt_template == INSTRUCTION_INPUT_RESPONSE_PATTERN:
            return f"### Instruction:\n{kwargs['system_info'] + kwargs['instruction']}\n" \
                   f"### Response: {kwargs['new_output_prefix']}"
        # elif self.prompt_template is of Phi-3 style:
            # return f"<|user|>\n{kwargs['direct_prompt']} <|end|>\n<|assistant|>"
        elif self.prompt_template == LLAMA3_PATTERN:
            return f"<|begin_of_text|>" \
                   f"<|start_header_id|>system<|end_header_id|>{kwargs['system_info']}<|eot_id|>" \
                   f"<|start_header_id|>user<|end_header_id|>{kwargs['instruction']}<|eot_id|>" \
                   f"<|start_header_id|>assistant<|end_header_id|>"
        else:
            raise NotImplementedError("Missing prompt template for used model")

    def _customized_model_post_process_output(self, output: str) -> str:
        if self.prompt_template == INSTRUCTION_INPUT_RESPONSE_PATTERN:
            output = output.split("### Response:")[1].strip().split("</s>")[0]
            output = output.removeprefix(f"{self.name}: ")
            time_and_name_prefix = f"] {self.name}: "
            if time_and_name_prefix in output:
                output = output.split(time_and_name_prefix)[1]
            return output.strip()
        elif self.prompt_template == LLAMA3_PATTERN:
            assistant_prefix = "<|start_header_id|>assistant<|end_header_id|>"
            if assistant_prefix in output:
                output = output.split(assistant_prefix)[1]
            return output.split("<|eot_id|>")[0].strip()
        else:
            raise NotImplementedError("Missing output template for used model")
