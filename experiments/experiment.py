"""
This file describes the base experiment class
"""
from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional, TYPE_CHECKING
from experiments.experiment_output import ExperimentOutput
from hosts import get_host_class
from persons import get_person_class
from end_types import get_end_type_class
import time
from session_rooms import get_session_room
from persons.batch.batch_person import BatchedPerson
from persons.person import Person

if TYPE_CHECKING:
    from hosts.host import Host
    from end_types.end_type import EndType
    from session_rooms.session_room import SessionRoom

log = logging.getLogger(__name__)


class Experiment:
    def __init__(self, persons: List[Person | BatchedPerson], session_room: SessionRoom, host: Host,
                 end_type: EndType, scenario: str, survey_questions: list[dict], *args, **kwargs):
        """
        Initialize the Experiment class
        :param persons: list of persons that are part of the experiment
        :param session_room: where the experiment us handled
        :param host: that will orchestrate the experiment
        :param end_type: that will use to decide if the experiment is over
        :param scenario: TODO: Add params explanation
        :param survey_questions: TODO: Add params explanation and define a type of survey questions
        """
        self.persons: List[Person] = persons
        self.session_room: SessionRoom = session_room
        self.end_type: EndType = end_type
        self.host: Host = host
        self.scenario = scenario
        self.survey_questions: list[dict] = survey_questions

    @classmethod
    def load_from_file(cls, file_path: str) -> Experiment:
        """
        Creates a new Experiment instance base on given file
        :param file_path: to parse
        :return: new Experiment instance
        """
        # TODO: parse multiple file types .yml and .json
        with open(file_path, 'r') as file:
            text = "".join(file.readlines())
        return cls.load_from_string(text)

    @staticmethod
    def _load_end_type(end_type_obj: Dict) -> Optional[EndType]:
        end_type_cls = get_end_type_class(end_type_obj.get("class"))
        if not end_type_cls:
            raise TypeError(f"No class type given in {end_type_obj}")
        return end_type_cls(**end_type_obj)

    @staticmethod
    def _load_persons(persons_list: List[Dict]) -> List[Person | BatchedPerson]:
        experiment_start_time = time.strftime("%H:%M:%S")
        persons: List[Person] = []
        for p_dict in persons_list:
            p_cls = get_person_class(p_dict.get("class"))
            if p_cls and issubclass(p_cls, Person):
                if p_dict.get("share_start_time", True):
                    p_dict["experiment_start_time"] = experiment_start_time
                try:
                    # using the extra and kwargs, is used by the DataFrame logger
                    log.info("Generating persons with", extra={"kwargs": p_dict})
                    persons.append(p_cls(**p_dict))
                except Exception as e:
                    log.info(f"Warning {p_dict} unable to create person", e)
                    raise e
            else:
                raise TypeError(f"No class type given in {p_dict}")

        if any([isinstance(p, BatchedPerson) for p in persons]):
            log.warning("Some persons are of type Ba")
        return persons

    @classmethod
    def _load_session_room(cls, session_room: dict | str = "base", experiment: Experiment | None = None) -> \
            'SessionRoom':
        if isinstance(session_room, str) or session_room is None:
            session_room = "base" if session_room is None else session_room
            return get_session_room(session_room)(experiment)
        elif isinstance(session_room, dict) and 'name' in session_room:
            return get_session_room(session_room.get("name"))(experiment, **session_room)
        else:
            raise TypeError("Unknown session_room type")

    @staticmethod
    def _load_host(host_obj: Dict, persons: List[Person]) -> Host:
        host_cls = get_host_class(host_obj.get("class"))
        if not host_cls:
            raise TypeError(f"No class type given in {host_cls}")
        return host_cls(**host_obj, persons=persons)

    @staticmethod
    def _load_experiment(experiment_obj: Dict, persons, session_room, host, end, survey_questions) -> Experiment:
        scenario = experiment_obj.get("scenario")
        if not scenario:
            raise TypeError("No scenario given")
        return Experiment(persons, session_room, host, end, scenario, survey_questions)

    @classmethod
    def load_from_string(cls, config_string: str):
        """
        Creates a new Experiment instance base on given string
        :param config_string: to parse
        :return: new Experiment instance
        """
        exp_config: Optional[Dict] = None
        try:
            exp_config = json.loads(config_string)
        except Exception:
            log.exception("Invalid Json")

        if not isinstance(exp_config, dict):
            raise TypeError()

        persons_obj: Optional[List[Dict[str, str]]] = exp_config.get("persons")
        session_room_obj = exp_config.get("sessionRoom")
        host_obj: Optional[Dict[str, str]] = exp_config.get("host")
        end_type_obj: Optional[Dict[str, str]] = exp_config.get("endType")
        experiment_type_obj: Optional[Dict[str, str]] = exp_config.get("experiment")

        if not persons_obj or not isinstance(persons_obj, list):
            raise TypeError("No persons")
        if not session_room_obj or not isinstance(session_room_obj, dict):
            log.warning("No SessionRoom using experiment default")
        if not host_obj or not isinstance(host_obj, dict):
            raise TypeError("No host")
        if not end_type_obj or not isinstance(end_type_obj, dict):
            raise TypeError("No end type")
        survey_questions = []
        if not experiment_type_obj and experiment_type_obj != {}:
            log.warning("No experiment type")
        elif not isinstance(experiment_type_obj, dict):
            raise TypeError("Invalid experiment type")
        else:
            survey_questions = experiment_type_obj.get("survey_questions", [])

        persons: List[Person] = cls._load_persons(persons_obj)
        session_room: SessionRoom = cls._load_session_room(session_room_obj, None)
        host: Host = cls._load_host(host_obj, persons)
        end: EndType = cls._load_end_type(end_type_obj)
        self = cls._load_experiment(experiment_type_obj, persons, session_room, host, end,
                                    survey_questions)
        session_room.experiment = self

        return self

    def run(self, save_session_file_name: str = None) -> ExperimentOutput:
        """
        Start the expiration
        @return:
        """
        assert self.session_room is not None
        return self.session_room.run(save_session_file_name)

    def export_file(self, path: str):
        """
        Export all the needed information of the experiment
        @param path:
        @return:
        """
        pass

    def has_survey_questions(self):
        return len(self.survey_questions) > 0

    # def __dict__(self):
    #     return {
    #         "host":self.host.__dict__,
    #         "persons": [p.__dict__ for p in self.persons],
    #         "endType": self.end_type.__dict__,
    #     }
