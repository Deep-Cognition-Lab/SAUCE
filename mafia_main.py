import json
import os
import sys
import time
from pathlib import Path

DIRS_PREFIX = "./mafia/games"
game_dir = Path(DIRS_PREFIX) / time.strftime("%d%m%y_%H%M")  # global variable
game_dir.mkdir(mode=0o777)


# files that host writes to and players read from
PLAYER_NAMES_FILE = "player_names.txt"
REMAINING_PLAYERS_FILE = "remaining_players.txt"
MAFIA_NAMES_FILE = "mafia_names.txt"
PHASE_STATUS_FILE = "phase_status.txt"
IS_GAME_OVER_FILE = "is_game_over.txt"
PUBLIC_MANAGER_CHAT_FILE = "public_manager_chat.txt"
PUBLIC_DAYTIME_CHAT_FILE = "public_daytime_chat.txt"
PUBLIC_NIGHTTIME_CHAT_FILE = "public_nighttime_chat.txt"
PERSONAL_CHAT_FILE_FORMAT = "{}_chat.txt"
PERSONAL_VOTE_FILE_FORMAT = "{}_vote.txt"
# # constant strings
NIGHTTIME = "NIGHTTIME"
GAME_OVER = "GAME_OVER"
# files that hosts read from and players write to
# TODO: are there any?

# game constants
NIGHTTIME_TIME_LIMIT_MINUTES = 2
NIGHTTIME_TIME_LIMIT_SECONDS = int(NIGHTTIME_TIME_LIMIT_MINUTES * 60)
DAYTIME_TIME_LIMIT_MINUTES = 5
DAYTIME_TIME_LIMIT_SECONDS = int(DAYTIME_TIME_LIMIT_MINUTES * 60)


def touch_file_in_game_dir(file_name):
    new_file = game_dir / file_name
    new_file.touch()
    return new_file


class Player:

    def __init__(self, name, is_mafia, is_model, **kwargs):
        self.name = name
        self.is_mafia = is_mafia
        self.is_model = is_model
        self.personal_chat_file = touch_file_in_game_dir(PERSONAL_CHAT_FILE_FORMAT.format(name))
        self.personal_chat_file_lines_read = 0
        self.personal_vote_file = touch_file_in_game_dir(PERSONAL_VOTE_FILE_FORMAT.format(name))
        self.is_still_in_game = True
        self.model = Model(name, is_mafia, is_model, **kwargs) if is_model else None

    def _create_personal_file(self, file_name):
        personal_file = game_dir / file_name
        personal_file.touch()
        return personal_file

    def get_new_messages(self):
        if not self.is_still_in_game:
            return []  # TODO maybe None? maybe not needed because won't reach here?
        if not self.is_model:
            with open(self.personal_chat_file, "r") as f:
                # the read lines method includes the "\n"
                lines = f.readlines()[self.personal_chat_file_lines_read:]
            self.personal_chat_file_lines_read += len(lines)
            return lines
        else:
            pass  # TODO !

    def get_voted_player(self):
        return self.personal_vote_file.read_text().strip()


class Model:

    def __init__(self, name, is_mafia, is_model, **kwargs):
        pass  # TODO !


# def create_game_dir():  # TODO: I moved to beginning as global var, delete func if not used
#     game_start_time = time.strftime("%d%m%y_%H%M")
#     game_dir = f"{DIRS_PREFIX}/{game_start_time}"
#     os.mkdir(game_dir, mode=0o777)
#     return game_dir


def init_game():
    with open(sys.argv[1]) as f:
        config = json.load(f)
    persons = config["persons"]
    players = [Player(**person) for person in persons]
    all_names_str = "\n".join([player.name for player in players])
    (game_dir / PLAYER_NAMES_FILE).write_text(all_names_str)
    (game_dir / REMAINING_PLAYERS_FILE).write_text(all_names_str)
    all_mafia_names_str = [player.name for player in players if player.is_mafia]
    (game_dir / MAFIA_NAMES_FILE).write_text("\n".join(all_mafia_names_str))
    (game_dir / PHASE_STATUS_FILE).write_text(NIGHTTIME)
    touch_file_in_game_dir(PUBLIC_MANAGER_CHAT_FILE)
    touch_file_in_game_dir(PUBLIC_DAYTIME_CHAT_FILE)
    touch_file_in_game_dir(PUBLIC_NIGHTTIME_CHAT_FILE)
    touch_file_in_game_dir(IS_GAME_OVER_FILE)
    return players


def is_game_over(players):  # TODO maybe on host side it shouldn't be reading of this file, but instead just a boolean flag that saves the file to notify players
    # TODO: if all mafia members died (maybe in future we can divide game-over to mafia win or bystanders win
    (game_dir / REMAINING_PLAYERS_FILE).read_text()  # TODO continue!!!

    return


def run_chat_round_between_players(players, chat_room):
    for player in players:
        lines = player.get_new_messages()
        with open(chat_room, "w") as f:
            f.writelines(lines)  # lines already include "\n"


def get_voted_out_player(voting_players, optional_votes_players):
    votes = {player.name: 0 for player in optional_votes_players}
    for player in voting_players:
        voted_for = player.get_voted_player()
        if voted_for in votes:
            votes[voted_for] += 1
    # if there were invalid votes or if there was a tie, decision will be made "randomly"
    voted_out_name = max(votes, key=votes.get)
    # update info file of remaining players
    remaining_players = (game_dir / REMAINING_PLAYERS_FILE).read_text().splitlines()
    remaining_players.remove(voted_out_name)
    (game_dir / REMAINING_PLAYERS_FILE).write_text("\n".join(remaining_players))
    # update player object status
    voted_out_player = {player.name: player for player in optional_votes_players}[voted_out_name]
    voted_out_player.is_still_in_game = False
    return voted_out_player


def run_phase(players, voting_players, optional_votes_players, public_chat_file, time_limit_seconds):
    start_time = time.time()
    while time.time() - start_time < time_limit_seconds:
        run_chat_round_between_players(voting_players, public_chat_file)
    voted_out_player = get_voted_out_player(voting_players, optional_votes_players)
    players.remove(voted_out_player)
    announce_voted_out_player(voted_out_player)  # TODO add a system message to the human interface (the one where all players can see) (PUBLIC_MANAGER_CHAT_FILE)


def run_nighttime(players):  # TODO validate these are only remaining players
    mafia_players = [player for player in players if player.is_mafia]  # and player.is_still_in_game]  # TODO maybe no need for check is_still_in_game because all of them already are
    bystanders = [player for player in players if not player.is_mafia]  # and player.is_still_in_game]  # TODO maybe no need for check is_still_in_game because all of them already are
    announce_nighttime()  # TODO all players should have the announcement of phase, time left, and who will be able to chat and read (PUBLIC_MANAGER_CHAT_FILE)
    run_phase(players, mafia_players, bystanders, game_dir / PUBLIC_NIGHTTIME_CHAT_FILE,
              NIGHTTIME_TIME_LIMIT_SECONDS)


def run_daytime(players):
    announce_daytime()  # TODO all players should have the announcement of phase, time left, and who will be able to chat and read (PUBLIC_MANAGER_CHAT_FILE)
    run_phase(players, players, players, game_dir / PUBLIC_DAYTIME_CHAT_FILE,
              DAYTIME_TIME_LIMIT_SECONDS)


def main():
    if len(sys.argv) != 2:
        raise ValueError(f"Usage: {__name__} <json configuration path>")  # TODO validate `__name__` works
    players = init_game()
    wait_for_players()
    while not is_game_over(players):
        run_nighttime(players)
        run_daytime(players)
    (game_dir / IS_GAME_OVER_FILE).write_text(GAME_OVER)
    run_end_of_game()


if __name__ == '__main__':
    main()
