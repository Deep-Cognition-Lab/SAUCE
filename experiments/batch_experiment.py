from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Union

from session_rooms import get_session_room
from persons import get_person_class

from persons.person import Person
from persons.batch.batcher import AutoBatchPerson
from .experiment import Experiment
from persons.batch.batch_person import BatchedPerson

if TYPE_CHECKING:
    from end_types.end_type import EndType
    from hosts.host import Host
    from session_rooms.session_room import SessionRoom
    from session_rooms.batch_session_room import BatchSessionRoom

log = logging.getLogger(__name__)


class BatchExperiment(Experiment):
    def __init__(self,
                 persons: list[BatchedPerson],
                 session_room: 'BatchSessionRoom',
                 host: Host,
                 end_type: EndType,
                 scenario: str,
                 survey_questions: list[dict],
                 *args, **kwargs):
        super().__init__(persons, session_room, host, end_type, scenario, survey_questions, *args, **kwargs)
        self.persons = persons
        self.session_room = session_room


    @staticmethod
    def _load_persons(persons_list: list[dict]) -> list[BatchedPerson]:
        persons: list[BatchedPerson] = []
        for p_dict in persons_list:
            p_cls = get_person_class(p_dict.get("class"))
            if p_cls is None:
                log.warning(f"there is no person of class {p_dict.get('class')}")
                log.info("skipping person")
                continue
            if issubclass(p_cls, BatchedPerson):
                log.info("Generating persons with", extra={"kwargs": p_dict})
                persons.append(p_cls(**p_dict))
            elif issubclass(p_cls, Person):
                log.info(f"Creating a batch version of {p_cls.__name__}")
                persons.append(AutoBatchPerson(**p_dict, person_class=p_cls))
        # validating the persons to be of type batch
        if not all([isinstance(person, BatchedPerson) for person in persons]):
            raise TypeError("In batch experiment we expect all persons to be of type BatchedPerson")
        # validate all persons have same batch size
        max_batch_person = max(persons, key=lambda p: p.batch_count)
        max_batch = max_batch_person.batch_count
        if not all([p.batch_count == max_batch for p in persons]):
            raise IndexError("In batch experiment we expect all person to have the same amount of background stories "
                             "and names")
        return persons

    @staticmethod
    def _load_experiment(experiment_obj: dict,
                         persons: list[BatchedPerson],
                         session_room,
                         host,
                         end,
                         survey_questions
                         ) -> BatchExperiment:
        scenario = experiment_obj.get("scenario")
        if not scenario:
            raise TypeError("No scenario given")
        return BatchExperiment(persons, session_room, host, end, scenario, survey_questions)

    @classmethod
    def _load_session_room(cls, session_room: dict | str = "batch", experiment: Experiment | None = None) -> 'SessionRoom':
        session_room_cls = None
        batch_base_class = get_session_room('batch')
        if isinstance(session_room, str) or session_room is None:
            session_room = "batch" if session_room is None else session_room
            session_room_cls = get_session_room(session_room)
        elif isinstance(session_room, dict) and 'name' in session_room:
            session_room_cls = get_session_room(session_room.get("name"))

        if not issubclass(session_room_cls, batch_base_class):
            raise TypeError("Session room in Batch experiment must be of batch type")

        return super()._load_session_room(session_room, experiment)

    @classmethod
    def load_from_string(cls, config_string: str) -> BatchExperiment:
        loaded_exp: BatchExperiment = super().load_from_string(config_string)
        log.debug(f"Updating session room batch size to {loaded_exp.persons[0].batch_count}")
        loaded_exp.session_room.batch_size = loaded_exp.persons[0].batch_count
        return loaded_exp
