from logic import SpaceController, StockInfoWithSqlite
import discord
import os
from discord import app_commands
from discord.ext import commands

sc = SpaceController()
st = StockInfoWithSqlite()

def show_stock_commands(bot, bot_msg, bot_defer):

    @bot.hybrid_command(name="주식", description="주가 보기")
    @app_commands.describe(
        name="회사명 or 티커 번호"
    )
    async def get_stock_price(ctx, name):
        name = sc.remove_space(name).upper()
        data = st.get_stock_info(name)
        set_ephemeral = False
        if str(os.getenv('ANGRY_KOKO')) in data:
            bot.add_log(ctx, "/주식", f"실패 // 입력 데이터: {name} // Exception: {data.split('$')[1].strip()}")
            data = data.split('$')[0].strip()
            set_ephemeral = True
        else:
            bot.add_log(ctx, "/주식", f"성공 // 입력 데이터: {name}")
        await bot_msg(ctx, data, ephemeral=set_ephemeral)

