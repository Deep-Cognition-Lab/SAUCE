from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from session_rooms.ChatEntry import ChatEntry


@dataclass
class SurveyQuestion:
    question_id:str
    question_content:str
    iteration:int
    chat_entry:list[ChatEntry]

