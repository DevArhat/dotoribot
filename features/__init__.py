from features.dotori_game import dotori_game_commands
from features.singing_dotori import singing_dotori_commands
from features.lostark_utils import lostark_utils_commands
from features.show_stock import show_stock_commands


__all__ = [
    "dotori_game_commands",
    "singing_dotori_commands",
    "lostark_utils_commands",
    "show_stock_commands",
    "load_all_commands"
]

def load_all_commands(bot, bot_msg):
    dotori_game_commands(bot, bot_msg)
    singing_dotori_commands(bot, bot_msg)
    lostark_utils_commands(bot, bot_msg)
    show_stock_commands(bot, bot_msg)
