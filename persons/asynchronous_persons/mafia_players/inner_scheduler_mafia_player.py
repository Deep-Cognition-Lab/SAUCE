from typing import List, TYPE_CHECKING
from persons.asynchronous_persons.inner_scheduler_asynchronous_person import \
    InnerSchedulerAsynchronousPerson
import logging
if TYPE_CHECKING:  # meant to protect cyclic imports caused from typing
    from session_rooms.session_room import ChatEntry

log = logging.getLogger(__name__)

PASS_TURN_TOKEN = "<pass>"
GAME_INSTRUCTIONS_PROMPT = "You are a player in the game of mafia. " \
                           "You are the current player to play. " \
                           "Here is the Game's history so far, " \
                           "with <player name> indicating the player's name, " \
                           "and <text> indicating that player's message. " \
                           "Completer your character's message after the last <text>:"
SCHEDULER_PROMPT_PREFIX = f"You are a player in the game of mafia. " \
                          f"Based on the following history, " \
                          f"decide whether to speak now or pass, using {PASS_TURN_TOKEN}."


class InnerSchedulerMafiaPlayer(InnerSchedulerAsynchronousPerson):

    def __init__(self, generation_model_name: str, inner_scheduler_model_path: str,
                 background_story: str, name: str, pass_turn_token: str = PASS_TURN_TOKEN,
                 **kwargs):
        super().__init__(background_story=background_story, name=name,
                         generation_model_name=generation_model_name,
                         inner_scheduler_model_name=inner_scheduler_model_path, **kwargs)
        self.pass_turn_token = pass_turn_token

    def create_context_for_scheduler(self, experiment_scenario_not_used, chat_list: List[ChatEntry]
                                     ) -> str:
        """
        Creates the context (chat history, prompt, scenario, etc.) used by the inner scheduler to
        decide whether to generate an answer.
        """
        if not chat_list:
            return ""
        chat_history = chat_list[-1].prompt.replace(GAME_INSTRUCTIONS_PROMPT, "")
        return f"{SCHEDULER_PROMPT_PREFIX} You're player name is {self.name}. " \
               f"The game's history: {chat_history.strip()} "

    def should_generate_answer(self, context: str) -> bool:
        """
        Decides whether to currently generate an answer, based on the context,
        using self.inner_scheduler_model.
        """
        if not context:
            return True  # No player has played yet, so first player can start
        scheduling_decision = self.inner_scheduler_model.generate(context)
        return bool(scheduling_decision.strip()) and \
            (self.generation_model.generate_without_special_tokens
             or self.pass_turn_token not in scheduling_decision)

    def create_prompt(self, experiment_scenario_not_used, chat_list: List[ChatEntry]) -> str:
        """Creates the prompt for the generation model,
        once the inner scheduler has decided it should"""
        if chat_list:
            prompt = chat_list[-1].prompt + chat_list[-1].answer.strip() + " "
        else:
            prompt = GAME_INSTRUCTIONS_PROMPT + " "
        return prompt + f"<player name> {self.name} <text> "
