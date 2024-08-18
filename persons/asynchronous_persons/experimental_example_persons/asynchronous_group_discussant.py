import time
from typing import Union, List
from persons.asynchronous_persons.inner_scheduler_asynchronous_person import \
    InnerSchedulerAsynchronousPerson
from session_rooms.session_room import ChatEntry
import logging

log = logging.getLogger(__name__)

PASS_TURN_TOKEN = "<wait>"
USE_TURN_TOKEN = "<speak>"
# prompts patterns:
INSTRUCTION_INPUT_RESPONSE_PATTERN = "instruction-input-response prompt pattern"
DEFAULT_PROMPT_PATTERN = "default"


class AsynchronousGroupDiscussant(InnerSchedulerAsynchronousPerson):
    PERSON_TYPE = "async_group_discussant"

    def __init__(self, background_story: str, name: str, opinion: str,
                 experiment_start_time: str,
                 in_context_learning: bool = False,
                 pass_turn_token: str = PASS_TURN_TOKEN,
                 use_turn_token: str = USE_TURN_TOKEN, **kwargs):
        super().__init__(background_story=background_story, name=name, **kwargs)
        self.prompt_template = self._get_prompt_template(self.generation_model_name)
        self.opinion = opinion
        self.experiment_start_time = experiment_start_time
        self.in_context_learning = in_context_learning
        self.pass_turn_token = pass_turn_token
        self.use_turn_token = use_turn_token

    def _get_prompt_template(self, model_name: str) -> str:  # TODO make static or extract to `person` utils
        model_name = model_name.lower()
        if "phi-3" in model_name:
            return INSTRUCTION_INPUT_RESPONSE_PATTERN
        # elif "____" in model_name: return "____"
        else:
            return DEFAULT_PROMPT_PATTERN

    def _create_customized_model_prompt_skeleton(self, **kwargs) -> str:
        if self.prompt_template == INSTRUCTION_INPUT_RESPONSE_PATTERN:
            return f"### Instruction:\n{kwargs['direct_prompt']}\n" \
                   f"### Response: {kwargs['new_output_prefix']}"
        # elif self.prompt_template is of Phi-3 style:
            # return f"<|user|>\n{kwargs['direct_prompt']} <|end|>\n<|assistant|>"
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
        else:
            raise NotImplementedError("Missing output template for used model")

    def _create_prompt_skeleton(self, experiment_scenario: str, chat_list: List[ChatEntry],
                                task: str) -> str:
        prompt = f"Your name is {self.name}. {self.background_story}\n" \
                 f"{experiment_scenario}\n{self.opinion}\n" \
                 f"The chat room was opened for discussion at [{self.experiment_start_time}].\n"
        if not chat_list:
            prompt += "No one has spoken yet.\n"
        else:
            prompt += "Here is the speaking history so far, including [timestamps]:\n"
            for chat_entry in chat_list:
                prompt += f"[{chat_entry.time}] {chat_entry.entity.name}: {chat_entry.answer}\n"
        current_timestamp = time.strftime("%H:%M:%S")
        prompt += f"The current time is [{current_timestamp}]. "
        prompt += task
        new_output_prefix = f"[{current_timestamp}] {self.name}: "  # won't be used by all models
        return self._create_customized_model_prompt_skeleton(direct_prompt=prompt,
                                                             new_output_prefix=new_output_prefix)

    def create_context_for_scheduler(self, experiment_scenario: str, chat_list: List[ChatEntry]
                                     ) -> str:
        """
        Creates the context (chat history, prompt, scenario, etc.) used by the inner scheduler to
        decide whether to generate an answer.
        """
        task = f"Do you want to speak now and add to the discussion, " \
               f"or do you prefer to wait for now and see what others will say? " \
               f"Reply only {self.use_turn_token} or {self.pass_turn_token} " \
               f"based on your decision!"
        if self.in_context_learning:
            task += f"\nHere is an example:\n" \
                    f"[10:35:40] Alex: Hello everyone! How are you?\n" \
                    f"[10:35:45] {self.name}: {self.use_turn_token}\n" \
                    f"Here is another example:\n" \
                    f"[14:23:01] Sam: Let me tell you how I see it.\n" \
                    f"[14:23:03] {self.name}: {self.pass_turn_token}\n" \
                    f"Here is another one:\n" \
                    f"[09:12:18] Ariel: That's how I see it. How do you feel about that?\n" \
                    f"[09:12:21] {self.name}: {self.use_turn_token}\n" \
                    f"One last example:\n" \
                    f"[17:00:57] Charlie: Let's hear what Nicole thinks.\n" \
                    f"[17:01:02] {self.name}: {self.pass_turn_token}"
        return self._create_prompt_skeleton(experiment_scenario, chat_list, task)

    def should_generate_answer(self, context: str) -> bool:
        """
        Decides whether to currently generate an answer, based on the context,
        using self.scheduling_model.
        """
        output = self.scheduling_model.generate(context)
        # log.debug(f"Raw scheduling decision was: \n'''\n{output}\n'''\n")
        scheduling_decision = self._customized_model_post_process_output(output)
        return bool(scheduling_decision.strip()) and \
            (self.generation_model.generate_without_special_tokens
             or self.pass_turn_token not in scheduling_decision)

    def create_prompt(self, experiment_scenario: str, chat_list: List[ChatEntry]) -> str:
        """Creates the prompt for the generation model,
        once the inner scheduler has decided it should"""
        task = "Add a short message to the conversation!"
        return self._create_prompt_skeleton(experiment_scenario, chat_list, task)

    def generate_answer(self, experiment_scenario: str, chat_list: List[ChatEntry]
                        ) -> Union[ChatEntry, None]:
        context = self.create_context_for_scheduler(experiment_scenario, chat_list)
        if self.should_generate_answer(context):
            log.info(f"Model chose to generate! ({self.name}'s turn)")
            prompt = self.create_prompt(experiment_scenario, chat_list)
            output = self.generation_model.generate(prompt)
            answer = self._customized_model_post_process_output(output)
            current_time = time.strftime("%H:%M:%S")
            return ChatEntry(entity=self, prompt=prompt, answer=answer, time=current_time)
        else:
            log.info(f"Model chose not to generate... ({self.name}'s turn)")
            return None
