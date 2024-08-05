from __future__ import annotations

import copy
import logging
from dataclasses import dataclass
from typing import List, Optional
import pickle
from experiments.experiment_output import ExperimentOutput
from experiments.survey_question import SurveyQuestion

# protect cyclic imports caused from typing
from typing import TYPE_CHECKING

from session_rooms.ChatEntry import ChatEntry

if TYPE_CHECKING:
    from experiments.experiment import Experiment
    from persons.person import Person

log = logging.getLogger(__name__)


class SessionRoom:
    def __init__(self, experiment: Optional[Experiment], *args, **kwargs):
        self.experiment: Experiment = experiment
        self.chat_room: List[ChatEntry] = []

    def run(self, save_session_file_name: str = None) -> ExperimentOutput:
        """ Runs the session room and returns the generated chat as a dataframe """
        log.info("Session room is running")

        output = ExperimentOutput()
        while not self.experiment.end_type.did_end(self):
            self.ask_survey_questions_if_needed(output)
            new_chat_entry = self.iterate()
            if new_chat_entry is not None:
                output.chat_entry.append(self.chat_room[-1])
        self.ask_survey_questions_if_needed(output)

        if save_session_file_name:
            with open(save_session_file_name, "wb") as file:
                pickle.dump(self, file)

        return output

    def ask_survey_questions_if_needed(self, experiment_output: ExperimentOutput):
        """
        Asks the survey questions that should be triggered at the current iteration.
        All persons participant in the survey and answers are stored in the
        `experiment_output`. This function does not modify `self.chat_room`.
        """

        # Keep only the survey questions that should be asked at the current iteration.
        should_keep = lambda cur_len, trigger: (cur_len in trigger) or \
                                               f"{trigger}".lower() == "always" or \
                                               (-1 in trigger and self.experiment.end_type.did_end(self))
        survey_questions = [q for q in self.experiment.survey_questions \
                            if should_keep(len(self.chat_room), q.get("iterations"))]

        if not survey_questions:
            return

        log.info("Starting survey. Everyone is answering this end_prompt:")
        for survey_question in survey_questions:
            experiment_output.survey_question.append(
                SurveyQuestion(
                    question_id=survey_question["id"],
                    question_content=survey_question["question"],
                    iteration=len(self.chat_room),
                    chat_entry=self.chat_room))

            survey_entry = ChatEntry(System(), "", survey_question["question"])
            log.info(survey_entry)
            # Copy the chat room, so it can later "forget" the survey question.
            chat_room_with_survery = copy.deepcopy(self.chat_room) + [survey_entry]

            for next_person in self.experiment.persons:
                new_chat_entry = next_person.generate_answer(
                    self.experiment.scenario, chat_room_with_survery)
                if new_chat_entry is not None:
                    experiment_output.survey_question[-1].chat_entry.append(
                        new_chat_entry)
                    log.info(new_chat_entry)

    @staticmethod
    def load_from_pickle(save_session_file_name: str) -> SessionRoom:
        with open(save_session_file_name, "rb") as file:
            loaded_session = pickle.load(file)
        return loaded_session

    def print_session(self) -> str:
        raise NotImplementedError("Need to be implanted")

    def iterate(self):
        next_person: Person = self.experiment.host.get_curr_person_and_move_to_next()
        new_chat_entry = next_person.generate_answer(
            self.experiment.scenario, self.chat_room)
        if new_chat_entry is not None:
            self.chat_room.append(new_chat_entry)
            log.info(new_chat_entry)
        return new_chat_entry

    @property
    def session_length(self) -> int:
        return len(self.chat_room)


@dataclass
class System:
    name = "System"