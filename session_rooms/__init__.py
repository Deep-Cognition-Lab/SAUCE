import logging

from typing import TYPE_CHECKING


from . import batch_session_room
from . import session_room

logging.getLogger(__name__).setLevel(logging.DEBUG)
if TYPE_CHECKING:
    from session_rooms.session_room import SessionRoom


def get_session_room(name: str) -> type['SessionRoom']:
    _dict = {
        "base": session_room.SessionRoom,
        "batch": batch_session_room.BatchSessionRoom
    }
    return _dict.get(name)
