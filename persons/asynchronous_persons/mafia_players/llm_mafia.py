import time
from typing import Union, List
from persons.asynchronous_persons.inner_scheduler_asynchronous_person import \
    InnerSchedulerAsynchronousPerson
from session_rooms.session_room import ChatEntry
from termcolor import colored
import logging

log = logging.getLogger(__name__)

PASS_TURN_TOKEN = "<wait>"
USE_TURN_TOKEN = "<speak>"


class LLMMafia(InnerSchedulerAsynchronousPerson):
    PERSON_TYPE = "llm_mafia"

    def __init__(self, background_story: str, name: str, role: str,
                 in_context_learning: bool = False,
                 pass_turn_token: str = PASS_TURN_TOKEN,
                 use_turn_token: str = USE_TURN_TOKEN, **kwargs):
        super().__init__(background_story=background_story, name=name, **kwargs)
        self.role = role if role is not None else "bystander"
        self.in_context_learning = in_context_learning
        self.experiment_start_time = kwargs.get("experiment_start_time", time.strftime("%H:%M:%S"))
        self.pass_turn_token = pass_turn_token
        self.use_turn_token = use_turn_token

    def _create_prompt_skeleton(self, experiment_scenario: str, chat_list: List[ChatEntry],
                                task: str) -> str:
        system_info = f"Your name is {self.name}. {self.background_story}\n" \
                      f"{experiment_scenario}\nYour role is {self.role}.\n" \
                      f"The chat room was opened for discussion at [{self.experiment_start_time}]."
        current_timestamp = time.strftime("%H:%M:%S")
        system_info += f"The current time is [{current_timestamp}].\n"
        if not chat_list:
            instruction = "No one has spoken yet.\n"
        else:
            instruction = "Here is the speaking history so far, including [timestamps]:\n"
            for chat_entry in chat_list:
                instruction += f"[{chat_entry.time}] {chat_entry.entity.name}: {chat_entry.answer}\n"
        instruction += task
        new_output_prefix = f"[{current_timestamp}] {self.name}: "  # won't be used by all models
        return self._create_customized_model_prompt_skeleton(system_info=system_info,
                                                             instruction=instruction,
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
        how_many_messages_by_it = sum([int(chat_entry.entity == self) for chat_entry in chat_list])
        if len(chat_list) > 7 and how_many_messages_by_it == 0:
            return self.use_turn_token
        elif len(chat_list) > 15 and how_many_messages_by_it < 2:
            task += f"Don't forget to choose {self.use_turn_token} once in a while!"
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
        using self.inner_scheduler_model.
        """
        if context == self.use_turn_token:
            return True
        output = self.inner_scheduler_model.generate(context)
        # log.debug(f"Raw scheduling decision was: \n'''\n{output}\n'''\n")
        scheduling_decision = self._customized_model_post_process_output(output)
        # log.warning(f"The model's post-processed scheduling_decision was: {scheduling_decision}")
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
        print(colored(f"{self.name}'s turn", "green"))
        context = self.create_context_for_scheduler(experiment_scenario, chat_list)
        if self.should_generate_answer(context):
            log.info(colored(f"Model chose to generate! ({self.name}'s turn)", "green"))
            prompt = self.create_prompt(experiment_scenario, chat_list)
            output = self.generation_model.generate(prompt)
            answer = self._customized_model_post_process_output(output)
            current_time = time.strftime("%H:%M:%S")
            return ChatEntry(entity=self, prompt=prompt, answer=answer, time=current_time)
        else:
            log.info(colored(f"Model chose not to generate... ({self.name}'s turn)", "green"))
            return None
