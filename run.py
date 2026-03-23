# tmux new -s bot
# tmux attach -t bot

from dotenv import load_dotenv

import os

from logic import add_log
from main import bot_run

load_dotenv()

def normal_logger(target, command, details='No Details'):
    add_log(target, command, details)

if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')
    print(f"[일반 모드] 로그인 중 . . .")
    bot_run(False, normal_logger)
