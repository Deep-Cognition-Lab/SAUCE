from __future__ import annotations
from typing import Type
import logging
import end_types.end_type
import end_types.message_num_type

logging.getLogger(__name__).setLevel(logging.DEBUG)


def get_end_type_class(name: str) -> Type[end_types.end_type.EndType]:
    _dict = {
        end_types.message_num_type.EndTypeNumMsgs.NAME: end_types.message_num_type.EndTypeNumMsgs
    }
    return _dict.get(name)
