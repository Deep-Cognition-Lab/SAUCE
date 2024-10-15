import json
import os
import sys
import time
from pathlib import Path
from persons.asynchronous_persons.mafia_players.llm_mafia import LLMMafia


# files that host writes to and players read from
DIRS_PREFIX = "./mafia/games"
PLAYER_NAMES_FILE = "player_names.txt"
REMAINING_PLAYERS_FILE = "remaining_players.txt"
MAFIA_NAMES_FILE = "mafia_names.txt"
PHASE_STATUS_FILE = "phase_status.txt"
WHO_WINS_FILE = "who_wins.txt"
PUBLIC_MANAGER_CHAT_FILE = "public_manager_chat.txt"
PUBLIC_DAYTIME_CHAT_FILE = "public_daytime_chat.txt"
PUBLIC_NIGHTTIME_CHAT_FILE = "public_nighttime_chat.txt"
PERSONAL_STATUS_FILE_FORMAT = "{}_status.txt"
# files that hosts read from and players write to
PERSONAL_CHAT_FILE_FORMAT = "{}_chat.txt"
PERSONAL_VOTE_FILE_FORMAT = "{}_vote.txt"
# constant strings for info files
NIGHTTIME = "NIGHTTIME"
DAYTIME = "DAYTIME"
VOTED_OUT = "VOTED_OUT"
MAFIA_ROLE = "mafia"
BYSTANDER_ROLE = "bystander"
MAFIA_WINS_MESSAGE = "Mafia wins!"
BYSTANDERS_WIN_MESSAGE = "Bystanders win!"
GAME_MANAGER_NAME = "Game-Manager"
RULES_OF_THE_GAME = "You are playing the game of Mafia. In the game each player is assigned a role secretly, either mafia or bystander. Every round a player is eliminated by the mafia during Nighttime, then during Daytime all remaining players discuss together who they think the mafia players are and vote out another player. The mafia's goal is to outnumber the bystanders, and the bystanders' goal it to vote out all real mafia."
# formats for saving texts
TIME_FORMAT_FOR_TIMESTAMP = "%H:%M:%S"
MESSAGE_FORMAT = "[{timestamp}] {name}: {message}"
VOTING_MESSAGE_FORMAT = "{} voted for {}"
VOTED_OUT_MESSAGE_FORMAT = "{} was voted out. Their role was {}"
# game constants
NIGHTTIME_TIME_LIMIT_MINUTES = 1  # 2
NIGHTTIME_TIME_LIMIT_SECONDS = int(NIGHTTIME_TIME_LIMIT_MINUTES * 60)
DAYTIME_TIME_LIMIT_MINUTES = 3  # 5
DAYTIME_TIME_LIMIT_SECONDS = int(DAYTIME_TIME_LIMIT_MINUTES * 60)
# global variable for the game dir
game_dir = Path()  # will be updated only if __name__ == __main__ (prevents new ones in imports)


def touch_file_in_game_dir(file_name):
    new_file = game_dir / file_name
    new_file.touch()
    return new_file


def get_role_string(is_mafia):
    return MAFIA_ROLE if is_mafia else BYSTANDER_ROLE


class Player:

    def __init__(self, name, is_mafia, is_model, **kwargs):
        self.name = name
        self.is_mafia = is_mafia
        self.is_model = is_model
        self.personal_chat_file = self._create_personal_file(PERSONAL_CHAT_FILE_FORMAT)
        self.personal_chat_file_lines_read = 0
        self.personal_vote_file = self._create_personal_file(PERSONAL_VOTE_FILE_FORMAT)
        self.personal_vote_file_last_modified = os.path.getmtime(self.personal_vote_file)
        # status is whether the player was vote out
        self.personal_status_file = self._create_personal_file(PERSONAL_STATUS_FILE_FORMAT)
        self.model = LLMMafia("", name, get_role_string(is_mafia), **kwargs) if is_model else None  # currently using "" as backstory...

    def _create_personal_file(self, file_name_format):
        return touch_file_in_game_dir(file_name_format.format(self.name))

    def get_new_messages(self):
        if not self.is_model:
            with open(self.personal_chat_file, "r") as f:
                # the readlines method includes the "\n"
                lines = f.readlines()[self.personal_chat_file_lines_read:]
            self.personal_chat_file_lines_read += len(lines)
            return lines
        else:
            chat_room = game_dir / PUBLIC_DAYTIME_CHAT_FILE   # TODO temporarily it is only for daytime, but should think of better mechanism in case model is mafia
            answer = self.model.generate_answer(RULES_OF_THE_GAME, chat_room.read_text().splitlines())
            return [answer] if answer is not None else []

    def get_voted_player(self):
        return self.personal_vote_file.read_text().strip()

    def did_cast_new_vote(self):
        last_modified = os.path.getmtime(self.personal_vote_file)
        if last_modified > self.personal_vote_file_last_modified:
            self.personal_vote_file_last_modified = last_modified
            return True
        else:
            return False

    def eliminate(self):
        self.personal_status_file.write_text(VOTED_OUT)


def init_game():
    global game_dir
    game_dir = Path(DIRS_PREFIX) / time.strftime("%d%m%y_%H%M")
    game_dir.mkdir(mode=0o777)
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
    touch_file_in_game_dir(WHO_WINS_FILE)
    return players


def is_win_by_bystanders(mafia_players):
    if len(mafia_players) == 0:
        (game_dir / WHO_WINS_FILE).write_text(BYSTANDERS_WIN_MESSAGE)
        return True
    return False


def is_win_by_mafia(mafia_players, bystanders):
    if len(mafia_players) >= len(bystanders):
        (game_dir / WHO_WINS_FILE).write_text(MAFIA_WINS_MESSAGE)
        return True
    return False


def is_game_over(players):
    mafia_players = [player for player in players if player.is_mafia]
    bystanders = [player for player in players if not player.is_mafia]
    return is_win_by_bystanders(mafia_players) or is_win_by_mafia(mafia_players, bystanders)


def format_message(name, message):
    timestamp = time.strftime(TIME_FORMAT_FOR_TIMESTAMP)
    return MESSAGE_FORMAT.format(timestamp=timestamp, name=name, message=message) + "\n"


def run_chat_round_between_players(players, chat_room):
    for player in players:
        lines = player.get_new_messages()
        with open(chat_room, "a") as f:
            f.writelines(lines)  # lines already include "\n"
        if player.did_cast_new_vote():
            # with open(game_dir / PUBLIC_MANAGER_CHAT_FILE, "a") as f:  # TODO validate chat_room is ok instead of PUBLIC_MANAGER_CHAT_FILE...
            with open(chat_room, "a") as f:
                voting_message = VOTING_MESSAGE_FORMAT.format(player.name, player.get_voted_player())
                f.write(format_message(GAME_MANAGER_NAME, voting_message))


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
    voted_out_player.eliminate()
    return voted_out_player


def announce_voted_out_player(voted_out_player):
    role = get_role_string(voted_out_player.is_mafia)
    with open(game_dir / PUBLIC_MANAGER_CHAT_FILE, "a") as f:
        voted_out_message = VOTED_OUT_MESSAGE_FORMAT.format(voted_out_player.name, role)
        f.write(format_message(GAME_MANAGER_NAME, voted_out_message))


def run_phase(players, voting_players, optional_votes_players, public_chat_file, time_limit_seconds):
    start_time = time.time()
    while time.time() - start_time < time_limit_seconds:
        run_chat_round_between_players(voting_players, public_chat_file)
    voted_out_player = get_voted_out_player(voting_players, optional_votes_players)
    players.remove(voted_out_player)
    announce_voted_out_player(voted_out_player)  # TODO add a system message to the human interface (the one where all players can see) (PUBLIC_MANAGER_CHAT_FILE) (maybe announce its role too?...)


def announce_nighttime():
    # TODO: implement better, this is temporary, maybe generalize a function for all manager messages (code duplicates...)
    with open(game_dir / PUBLIC_MANAGER_CHAT_FILE, "a") as f:
        phase_message = f"Now it's Nighttime for {NIGHTTIME_TIME_LIMIT_MINUTES} minutes, " \
                        f"only mafia can communicate and see messages and votes."  # TODO make constant
        f.write(format_message(GAME_MANAGER_NAME, phase_message))


def run_nighttime(players):  # TODO validate these are only remaining players
    (game_dir / PHASE_STATUS_FILE).write_text(NIGHTTIME)
    mafia_players = [player for player in players if player.is_mafia]
    bystanders = [player for player in players if not player.is_mafia]
    announce_nighttime()  # TODO all players should have the announcement of phase, time left, and who will be able to chat and read (PUBLIC_MANAGER_CHAT_FILE)
    run_phase(players, mafia_players, bystanders, game_dir / PUBLIC_NIGHTTIME_CHAT_FILE,
              NIGHTTIME_TIME_LIMIT_SECONDS)


def announce_daytime():
    # TODO: implement better, this is temporary, maybe generalize a function for all manager messages (code duplicates...)
    with open(game_dir / PUBLIC_MANAGER_CHAT_FILE, "a") as f:
        phase_message = f"Now it's Daytime for {DAYTIME_TIME_LIMIT_MINUTES} minutes, " \
                        f"everyone can communicate and see messages and votes."  # TODO make constant
        f.write(format_message(GAME_MANAGER_NAME, phase_message))


def run_daytime(players):
    (game_dir / PHASE_STATUS_FILE).write_text(DAYTIME)
    announce_daytime()  # TODO all players should have the announcement of phase, time left, and who will be able to chat and read (PUBLIC_MANAGER_CHAT_FILE)
    run_phase(players, players, players, game_dir / PUBLIC_DAYTIME_CHAT_FILE,
              DAYTIME_TIME_LIMIT_SECONDS)


def wait_for_players(players):
    # TODO: this is only temporary,
    #  maybe use something automatic, like all players need to sign up in their files...
    input("As game manager, use Enter to start the game after all players have entered: ")
    print("Game is now running! It's content is displayed to players.")


def end_game():
    print("Game has finished.")  # TODO: maybe log the game somehow? maybe save important details?..


def main():
    if len(sys.argv) != 2:
        raise ValueError(f"Usage: {Path(__file__).name} <json configuration path>")
    players = init_game()
    wait_for_players(players)
    while not is_game_over(players):
        run_nighttime(players)
        run_daytime(players)
    end_game()


if __name__ == '__main__':
    main()
