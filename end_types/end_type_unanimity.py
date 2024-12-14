"""
This file implements the EndType based on unanimity.
"""

from __future__ import annotations

from end_types.end_type import EndType
# Protect cyclic imports caused from typing
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from session_rooms.session_room import SessionRoom

class EndTypeUnanimity(EndType):
    """
    EndType that ends when all jurors agree (unanimity) at the end of a round (or max number of messages).
    """
    NAME = "unanimity"

    def __init__(self, max_num_msgs: int, *args, **kwargs):
        """
        Initialize with a maximum number of messages.
        """
        super().__init__(*args, **kwargs)
        self.max_num_msgs = max_num_msgs
        self.unanimity_status = None

    def is_unanimous(self, session_room: SessionRoom):
        """
        Checks if the current round of votes is unanimous.

        This method determines whether the most recent message completes a round of votes,
        then checks for unanimity across the latest round.

        :param session_room: The session room containing the chat and experiment data.
        :return: True if the current round is unanimous, False otherwise.
        """

        num_jurors = len(session_room.experiment.persons)

        if not session_room.chat_room:
            return False

        # Get the latest message's vote
        last_message = session_room.chat_room[-1].answer.strip()
        current_entity = session_room.chat_room[-1].entity
        print(f"Processing vote: {last_message}, Entity: {current_entity}")  # Debug

        # Error handle invalid input (for the main flow, not survey)
        if last_message[0] not in "01":
            raise ValueError("Invalid input: Votes must start with '0' (not guilty) or '1' (guilty).")

        # Check if this is the end of the round
        if current_entity == session_room.experiment.persons[-1]:
            votes = [message.answer.strip()[0] for message in session_room.chat_room[-num_jurors:]]
            self.unanimity_status = votes
            print(f"\033[92mRound votes: {votes}\033[0m")  # Debug: Show current round votes (Green)

            # Check for unanimity
            if all(vote == votes[0] for vote in votes):
                self.unanimity_status = "Guilty" if votes[0] == "1" else "Not Guilty"
                return True

            print(f"\033[91mUnanimity Not Reached.\033[0m")  # Debug: Show current round votes (Green)

        return False

    def did_end(self, session_room: SessionRoom) -> bool:
        """
        Determines whether the session should end.

        The session ends if either:
        1. Unanimity is reached in the latest round of votes.
        2. The maximum number of messages has been reached.

        :param session_room: The session room containing the chat and experiment data.
        :return: True if the session should end, False otherwise.
        """

        if self.is_unanimous(session_room):
            print(f"\033[92mUnanimity reached: {self.unanimity_status}\033[0m")
            return True

        # Fallback: Check max message limit
        if session_room.session_length >= self.max_num_msgs:
            print(f"\033[93mMaximum allowed number of messages reached.\033[0m")  # Yellow for warning
            return True

        return False
