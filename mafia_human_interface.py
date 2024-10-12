import os
from pathlib import Path
from mafia_main import DIRS_PREFIX, PLAYER_NAMES_FILE, MAFIA_NAMES_FILE, PHASE_STATUS_FILE, \
    NIGHTTIME, WHO_WINS_FILE, PUBLIC_MANAGER_CHAT_FILE, PUBLIC_DAYTIME_CHAT_FILE, \
    PUBLIC_NIGHTTIME_CHAT_FILE, PERSONAL_CHAT_FILE_FORMAT, PERSONAL_VOTE_FILE_FORMAT, \
    REMAINING_PLAYERS_FILE, format_message, VOTED_OUT, PERSONAL_STATUS_FILE_FORMAT, \
    RULES_OF_THE_GAME
from termcolor import colored
from threading import Thread

# output colors
MANAGER_COLOR = "green"
DAYTIME_COLOR = "light_blue"
NIGHTTIME_COLOR = "red"
# user messages
WELCOME_MESSAGE = "Welcome to the game of Mafia!"
GET_USER_NAME_MESSAGE = "Who are you? Enter the name's number: "
VOTE_FLAG = "VOTE"
GET_INPUT_MESSAGE = f"Enter a message to public chat, or '{VOTE_FLAG}' to cast a vote: "
GET_VOTED_NAME_MESSAGE = "Make your vote! You can change your vote until elimination is done." \
                         "Enter your vote's number: "
ROLE_REVELATION_MESSAGE = "Your role in the game is:"
YOU_CANT_WRITE_MESSAGE = "You were voted out and can no longer write messages."


# global variable
input(colored("Press enter only after the main game code started running...",  # to get latest dir
              MANAGER_COLOR))
game_dir = max(Path(DIRS_PREFIX).glob("*"), key=os.path.getmtime)  # latest modified dir


def get_player_names_by_id(player_names_file):
    player_names = (game_dir / player_names_file).read_text().splitlines()
    return {f"{i}": name for i, name in enumerate(player_names) if name}


def get_player_name_from_user(optional_player_names_file, input_message):
    player_names_by_id = get_player_names_by_id(optional_player_names_file)
    name_id = ""
    enumerated_names = ",   ".join([f"{i}: {name}" for i, name in player_names_by_id.items()])
    while name_id not in player_names_by_id:
        name_id = input(colored(f"{input_message}\n{enumerated_names} ",
                                MANAGER_COLOR))
    name = player_names_by_id[name_id]
    return name


def get_is_mafia(name):
    mafia_names = (game_dir / MAFIA_NAMES_FILE).read_text().splitlines()  # removes the "\n"
    return name in mafia_names


def is_nighttime():
    return NIGHTTIME in (game_dir / PHASE_STATUS_FILE).read_text()


def is_game_over():
    return bool((game_dir / WHO_WINS_FILE).read_text())  # if someone wins, the file isn't empty


def is_voted_out(name):
    return VOTED_OUT in (game_dir / PERSONAL_STATUS_FILE_FORMAT.format(name)).read_text()


def display_lines_from_file(file_name, num_read_lines, display_color):
    with open(game_dir / file_name, "r") as f:
        lines = f.readlines()[num_read_lines:]
    if len(lines) > 0:  # TODO if print() is deleted then remove this if!
        # print()  # prevents the messages from being printed in the same line as the middle of input  # TODO validate it's not needed and delete if so
        for line in lines:
            print(colored(line, display_color))  # TODO maybe need display_line func for special format?
    return len(lines)


def read_game_text(is_mafia):
    num_read_lines_manager = num_read_lines_daytime = num_read_lines_nighttime = 0
    while not is_game_over():
        num_read_lines_manager += display_lines_from_file(
            PUBLIC_MANAGER_CHAT_FILE, num_read_lines_manager, MANAGER_COLOR)
        # only current phase file will have new messages, so no need to run expensive is_nighttime()
        num_read_lines_daytime += display_lines_from_file(
            PUBLIC_DAYTIME_CHAT_FILE, num_read_lines_daytime, DAYTIME_COLOR)
        if is_mafia:  # only mafia can see what happens during nighttime
            num_read_lines_nighttime += display_lines_from_file(
                PUBLIC_NIGHTTIME_CHAT_FILE, num_read_lines_nighttime, NIGHTTIME_COLOR)


def collect_vote(name):
    voted_name = get_player_name_from_user(REMAINING_PLAYERS_FILE, GET_VOTED_NAME_MESSAGE)
    (game_dir / PERSONAL_VOTE_FILE_FORMAT.format(name)).write_text(voted_name)


def write_text_to_game(name, is_mafia):
    while not is_game_over():
        if is_voted_out(name):
            print(colored(YOU_CANT_WRITE_MESSAGE, MANAGER_COLOR))
            break  # can't write or vote anymore (but can still read the game's content)
        if not is_mafia and is_nighttime():
            continue  # only mafia can communicate during nighttime
        user_input = input(colored(GET_INPUT_MESSAGE, MANAGER_COLOR)).strip()
        if user_input.lower() == VOTE_FLAG.lower():  # lower for robustness, even though it's caps
            collect_vote(name)
        else:
            with open(game_dir / PERSONAL_CHAT_FILE_FORMAT.format(name), "a") as f:
                f.write(format_message(name, user_input))


def game_read_and_write_loop(name, is_mafia):
    # # TODO: if this works, maybe try to switch: write_text_to_game will be daemon, so we can "return" after is_voted_out instead of continuing reading the file again and again
    # read_thread = Thread(target=read_game_text, args=(is_mafia,))
    # # daemon: reading will be "behind scenes" and will allow writing to be stopped (e.g. by Ctrl+C)
    # read_thread.daemon = True
    # read_thread.start()
    # write_text_to_game(name, is_mafia)   # TODO remove this section if it works
    write_thread = Thread(target=write_text_to_game, args=(name, is_mafia))
    # daemon: writing in the background, so it can stop when eliminated and still allow reading
    write_thread.daemon = True
    write_thread.start()
    read_game_text(is_mafia)


def welcome_player():
    print(colored(WELCOME_MESSAGE, MANAGER_COLOR))
    print(colored(RULES_OF_THE_GAME, MANAGER_COLOR))
    name = get_player_name_from_user(PLAYER_NAMES_FILE, GET_USER_NAME_MESSAGE)
    is_mafia = get_is_mafia(name)
    role = "mafia" if is_mafia else "bystander"
    role_color = NIGHTTIME_COLOR if is_mafia else DAYTIME_COLOR
    print(colored(ROLE_REVELATION_MESSAGE, MANAGER_COLOR), colored(role, role_color))
    return name, is_mafia


def game_over_message():
    who_wins = (game_dir / WHO_WINS_FILE).read_text().strip()
    print(colored(who_wins, MANAGER_COLOR))
    mafia_names = (game_dir / MAFIA_NAMES_FILE).read_text().splitlines()  # removes the "\n"
    mafia_revelation = f"Mafia members were: " + ",".join(mafia_names)
    print(colored(mafia_revelation, MANAGER_COLOR))


def main():
    # TODO this part until around END should be in welcome_player() func (decide after choosing what it returns)
    name, is_mafia = welcome_player()
    game_read_and_write_loop(name, is_mafia)
    game_over_message()


if __name__ == '__main__':
    main()

# TODO: comments after first run:
#  * shouldn't add print() before empty lines... it's too much
#  * maybe manager messages of votes should be in red/light blue (because only mafia should see at nighttime)

# TODO remove if parallelism works
"""
The following is a piece of code that might solve my problem of reading and writing on the same time (+/-, the message is still cut in the middle if typing when it reads something...)
"""

r"""
import threading
import time
import os

READ_PATH = "/homes/nive/scripts/read_try.txt"
WRITE_PATH = "/homes/nive/scripts/write_try.txt"


def reading_func(reading_path):
    num_read_lines = 0
    while True:
        with open(reading_path, "r") as f:
            lines = f.readlines()[num_read_lines:]
        if len(lines) > 0:
            print()  # prevents the messages from being printed in the same line as the middle of writing
            for line in lines:
                print(f"read line: {line.strip()}")
        num_read_lines += len(lines)


def writing_func(writing_path):
    while True:
        user_input = input("Enter text to write (or 'q' to quit):\n").strip()
        if not user_input:
            continue
        if user_input.lower() == 'q':
            break
        with open(writing_path, 'a') as f:
            f.write(user_input + '\n')



def main():
    read_thread = threading.Thread(target=reading_func, args=(READ_PATH,))
    read_thread.daemon = True  # reading will be "behind scenes" and will allow write to be stopped (e.g. by Ctrl+C)
    read_thread.start()

    writing_func(WRITE_PATH)



if __name__ == "__main__":
    main()
"""