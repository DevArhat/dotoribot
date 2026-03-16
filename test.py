import os
from dotenv import load_dotenv
from main import bot_run
from logic import add_test_log

load_dotenv()

def test_logger(target, command, details='No Details'):
    add_test_log(target, command, details)
    
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN_TEST')
    print(f"[테스트 모드] 로그인 중 . . .")
    bot_run(True, test_logger)
