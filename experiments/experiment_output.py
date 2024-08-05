from __future__ import annotations

import json

from typing import TYPE_CHECKING
from dataclasses import dataclass,asdict,field

if TYPE_CHECKING:
    from experiments.survey_question import SurveyQuestion
    from session_rooms.ChatEntry import ChatEntry


@dataclass
class ExperimentOutput:
    chat_entry:list['ChatEntry'] = field(default_factory=list)
    survey_question: list['SurveyQuestion'] = field(default_factory=list)

    def __json__(self):
        return asdict(self)
    
    @classmethod
    def from_json(cls,source:dict | str):
        d = source if isinstance(source,dict) else json.loads(source)
        return cls(d)
