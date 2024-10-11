import os
from pathlib import Path
from mafia_main import DIRS_PREFIX, PLAYER_NAMES_FILE, MAFIA_NAMES_FILE, PHASE_STATUS_FILE, \
    NIGHTTIME, IS_GAME_OVER_FILE, GAME_OVER, PUBLIC_MANAGER_CHAT_FILE, PUBLIC_DAYTIME_CHAT_FILE, \
    PUBLIC_NIGHTTIME_CHAT_FILE, PERSONAL_CHAT_FILE_FORMAT, PERSONAL_VOTE_FILE_FORMAT, \
    REMAINING_PLAYERS_FILE
from termcolor import colored
from threading import Thread

# output colors
MANAGER_COLOR = "green"
DAYTIME_COLOR = "light_blue"
NIGHTTIME_COLOR = "red"
# user messages
WELCOME_MESSAGE = "Welcome to the game of Mafia!"
GET_USER_NAME_MESSAGE = "Who are you? Enter the name's number:"
GET_VOTED_NAME_MESSAGE = "Make your vote! You can change your vote until elimination is done." \
                         "Enter your vote's number:"


# global variable
input("Press enter only after the main game code started running...")  # to get the latest one  # TODO make in color
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
    player_names = (game_dir / PLAYER_NAMES_FILE).read_text().splitlines()
    return name in player_names


def is_nighttime():  # TODO maybe not needed?.....
    return NIGHTTIME in (game_dir / PHASE_STATUS_FILE).read_text()


def is_game_over():
    return GAME_OVER in (game_dir / IS_GAME_OVER_FILE).read_text()


def display_lines_from_file(file_name, num_read_lines, display_color):
    with open(game_dir / file_name, "r") as f:
        lines = f.readlines()[num_read_lines:]
    if len(lines) > 0:
        print()  # prevents the messages from being printed in the same line as the middle of input
        for line in lines:
            display_line(line, display_color)  # TODO: print with colored, but include processing of the format


def read_game_text():
    num_read_lines_manager = num_read_lines_daytime = num_read_lines_nighttime = 0
    while not is_game_over():
        num_read_lines_manager += display_lines_from_file(
            PUBLIC_MANAGER_CHAT_FILE, num_read_lines_manager, MANAGER_COLOR)
        num_read_lines_daytime += display_lines_from_file(
            PUBLIC_DAYTIME_CHAT_FILE, num_read_lines_daytime, DAYTIME_COLOR)
        num_read_lines_nighttime += display_lines_from_file(
            PUBLIC_NIGHTTIME_CHAT_FILE, num_read_lines_nighttime, NIGHTTIME_COLOR)


def collect_vote(name):
    voted_name = get_player_name_from_user(REMAINING_PLAYERS_FILE, GET_VOTED_NAME_MESSAGE)
    (game_dir / PERSONAL_VOTE_FILE_FORMAT.format(name)).write_text(voted_name)


def write_text_to_game(name):
    while not is_game_over():
        user_input = input(colored(GET_INPUT_MESSAGE, MANAGER_COLOR)).strip()
        if user_input == VOTE_FLAG:
            collect_vote(name)
        else:
            with open(game_dir / PERSONAL_CHAT_FILE_FORMAT.format(name), "a") as f:
                f.write(user_input + "\n")  # TODO: maybe writeline works too? maybe nicer than +"\n"?


def game_read_and_write_loop(name):
    read_thread = Thread(target=read_game_text, args=())
    # daemon: reading will be "behind scenes" and will allow writing to be stopped (e.g. by Ctrl+C)
    read_thread.daemon = True
    read_thread.start()
    write_text_to_game(name)


def main():
    # TODO this part until around END should be in welcome_player() func (decide after choosing what it returns)
    print(colored(WELCOME_MESSAGE, MANAGER_COLOR))
    name = get_player_name_from_user(PLAYER_NAMES_FILE, GET_USER_NAME_MESSAGE)
    is_mafia = get_is_mafia(name)
    welcome_message(is_mafia)
    game_read_and_write_loop(name)
    while True:
        if is_nighttime and is_mafia:
            pass
        elif not is_nighttime:
            pass
        else:  # it is nighttime but player is a bystander
            continue


if __name__ == '__main__':
    main()


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