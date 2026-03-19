from features.dotori_game import dotori_game_commands
from features.dotori_stock import dotori_stock_commands
from features.kakao_map_utils import kakao_map_utils_commands
from features.lostark_utils import lostark_utils_commands
from features.show_stock import show_stock_commands
from features.singing_dotori import singing_dotori_commands



__all__ = [
    "load_all_commands"
]

def load_all_commands(bot, bot_msg, bot_defer):
    bot_func = (bot, bot_msg, bot_defer)
    dotori_game_commands(*bot_func)
    dotori_stock_commands(*bot_func)
    kakao_map_utils_commands(*bot_func)
    lostark_utils_commands(*bot_func)
    show_stock_commands(*bot_func)
    singing_dotori_commands(*bot_func)