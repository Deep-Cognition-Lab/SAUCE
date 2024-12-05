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
        self.max_num_msgs = max_num_msgs
        self.completed_rounds = []  # Store completed rounds of votes
        self.current_round_votes = []  # Track votes in the current round
        self.is_unanimous = False  # Tracks whether unanimity has been reached

    def handle_votes(self, session_room: SessionRoom):
        """
        Collects votes from the latest message in the session and tracks complete rounds.
        """
        num_jurors = len(session_room.experiment.persons)

        # Get the latest message's vote
        if session_room.chat_room:
            last_message = session_room.chat_room[-1].answer.strip()
            print(f"\033[92mProcessing vote: {last_message}\033[0m")  # Debug: Show the vote being processed (Green)

            # Error handle invalid input (for the main flow, not survey)
            if last_message[0] not in "01":
                raise ValueError("Invalid input: Votes must start with '0' (not guilty) or '1' (guilty).")

            # Append vote to current round
            self.current_round_votes.append(last_message[0])
            print(
                f"\033[92mCurrent round votes: {self.current_round_votes}\033[0m")  # Debug: Show current round state (Green)

            # If the current round is complete, move it to completed rounds
            if len(self.current_round_votes) == num_jurors:
                self.completed_rounds.append(self.current_round_votes)
                print(f"\033[92mCompleted round: {self.completed_rounds[-1]}\033[0m")  # Debug: Show completed round (Green)
                self.current_round_votes = []  # Reset for the next round

    def check_unanimity(self) -> bool:
        """
        Check if the latest completed round is unanimous.
        :return: True if the last completed round is unanimous, False otherwise.
        """
        if self.completed_rounds:
            last_round = self.completed_rounds[-1]
            return all(vote == last_round[0] for vote in last_round)
        return False

    def did_end(self, session_room: SessionRoom, is_unanimity_experiment: bool = False) -> bool:
        """
        Ends when all jurors agree in the latest complete round or max messages are reached.

        :param is_unanimity_experiment: Flag to determine if this is an experiment (True) or survey (False).
        """
        if is_unanimity_experiment:
            # Process the latest vote and track rounds
            self.handle_votes(session_room)

            # Update the unanimity status
            self.is_unanimous = self.check_unanimity()

        # Always check if unanimity has been reached
        if self.is_unanimous:
            print(f"\033[92mUnanimity reached: {self.completed_rounds[-1]}\033[0m")  # Debug: Show unanimous decision (Green)
            return True

        # Fallback: Check max message limit
        return session_room.session_length >= self.max_num_msgs
