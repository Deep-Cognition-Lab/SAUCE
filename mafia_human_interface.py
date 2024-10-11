import os
from pathlib import Path
from mafia_main import DIRS_PREFIX, PLAYER_NAMES_FILE, MAFIA_NAMES_FILE, PHASE_STATUS_FILE, NIGHTTIME


# global variable
input("Press enter only after the main game code started running...")  # to get the latest one  # TODO make in color
game_dir = max(Path(DIRS_PREFIX).glob("*"), key=os.path.getmtime)  # latest modified dir


def get_player_names_by_id():
    player_names = (game_dir / PLAYER_NAMES_FILE).read_text().splitlines()
    return {f"{i}": name for i, name in enumerate(player_names) if name}


def get_is_mafia(name):
    player_names = (game_dir / PLAYER_NAMES_FILE).read_text().splitlines()
    return name in player_names


def get_is_nighttime():
    return NIGHTTIME in (game_dir / PHASE_STATUS_FILE).read_text()


def main():
    player_names_by_id = get_player_names_by_id()
    name_id = ""
    enumerated_names = ",   ".join([f"{i}: {name}" for i, name in player_names_by_id.items()])
    while name_id not in player_names_by_id:
        name_id = input(f"Who are you? Enter the name's number:\n{enumerated_names} ")
    name = player_names_by_id[name_id]
    is_mafia = get_is_mafia(name)
    welcome_message(is_mafia)
    while True:
        is_nighttime = get_is_nighttime()
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