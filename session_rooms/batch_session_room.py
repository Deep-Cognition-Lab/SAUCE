from __future__ import annotations

import logging
import pickle
from typing import TYPE_CHECKING

from experiments.experiment_output import ExperimentOutput
from experiments.survey_question import SurveyQuestion
from .ChatEntry import ChatEntry
from .session_room import SessionRoom, System

if TYPE_CHECKING:
    from experiments.batch_experiment import BatchExperiment

log = logging.getLogger(__name__)


class BatchSessionRoom(SessionRoom):
    def __init__(self, experiment: BatchExperiment | None, batch_size: int = 0):
        super().__init__(experiment)
        self._batch_size = batch_size
        self.chat_rooms = [[] for _ in range(self.batch_size)] if batch_size != 0 else []

    def run(self, save_session_file_name: str = None) -> list[ExperimentOutput]:
        log.info("Starting batch session (batch size %d)", self.batch_size)

        outputs = [ExperimentOutput() for _ in range(self.batch_size)]
        while not self.experiment.end_type.did_end(self):
            self.ask_survey_questions_if_needed(outputs)
            self.iterate()
            for i, room in enumerate(self.chat_rooms):
                outputs[i].chat_entry.append(room[-1])
        self.ask_survey_questions_if_needed(outputs)
        if save_session_file_name:
            with open(save_session_file_name, "wb") as file:
                pickle.dump(self, file)

        log.info("Session room is done.")
        return outputs

    def ask_survey_questions_if_needed(self, outputs: list[ExperimentOutput]) -> None:
        """
        Asks the survey questions that should be triggered at the current iteration.
        All persons participant in the survey and answers are stored in the
        `experiment_output`. This function does not modify `self.chat_room`.
        """
        for experiment_output in outputs:
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
                for i in range(len(self.chat_rooms)):
                    # Copy the chat room, so it can later "forget" the survey question.
                    self.chat_rooms[i].append(survey_entry)

                for next_person in self.experiment.persons:
                    new_chat_entry = next_person.generate_answer(
                        self.experiment.scenario, self.chat_rooms)
                    if new_chat_entry is not None:
                        experiment_output.survey_question[-1].chat_entry.append(
                            new_chat_entry)
                        log.info(new_chat_entry)
                # remove the question
                for chat_room in self.chat_rooms:
                    chat_room.pop()

    def iterate(self):
        next_person = self.experiment.host.get_curr_person_and_move_to_next()
        new_chat_entries = next_person.generate_answer(
            self.experiment.scenario, self.chat_rooms)

        for i, room in enumerate(self.chat_rooms):
            room.append(new_chat_entries[i])

        for idx, entry in enumerate(new_chat_entries):
            log.info(f"{idx}-{entry}")

    @property
    def session_length(self) -> int:
        return len(min(self.chat_rooms, key=lambda room: len(room)))

    @property
    def batch_size(self) -> int:
        return self._batch_size

    @batch_size.setter
    def batch_size(self, batch_size: int):
        rooms_len = len(self.chat_rooms)
        if batch_size > rooms_len:
            for _ in range(batch_size - rooms_len):
                self.chat_rooms.append([])
            self._batch_size = batch_size
        else:
            raise ValueError("Batch size must be less than or equal to the current number of chat rooms.")
