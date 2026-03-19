import discord
from discord import app_commands
from discord.ext import commands

from logic import LostArkGuardian, SpaceController, calc_logic, calc_logic_v2

sc = SpaceController()

def lostark_utils_commands(bot, bot_msg, bot_defer):

    @bot.hybrid_command(name="이번주가디언", description="이번주 가디언 정보")
    async def send_weekly_guardian_info(ctx):
        bot.add_log(ctx, "/이번주가디언")
        g = LostArkGuardian().get_lostark_weekly_info()
        add_msg = ''
        if g[1] == "스콜라키아":
            add_msg = '안녕하세요이슬비기상술사입니다스콜은제가배럭으로도자주찾는가디언이고제가사랑하는정말경이로운가디언이죠이쿨감의매력을이천삼십년저와함께찾아보시지않겠어요스콜에서만나요편린을위하여다함께나가자1750가디언스콜라키아'
        msg = (f"# {g[1]} ({g[2]})\n{g[0]}\n{add_msg}")
        await bot_msg(ctx, msg)

    @bot.hybrid_command(name="다음주가디언", description="다음주 가디언 정보")
    async def send_next_week_guardian_info(ctx):
        bot.add_log(ctx, "/다음주가디언")
        g = LostArkGuardian().get_lostark_weekly_info()
        add_msg = ''
        if g[4] == "스콜라키아":
            add_msg = '안녕하세요이슬비기상술사입니다스콜은제가배럭으로도자주찾는가디언이고제가사랑하는정말경이로운가디언이죠이쿨감의매력을이천삼십년저와함께찾아보시지않겠어요스콜에서만나요편린을위하여다함께나가자1750가디언스콜라키아'
        
        msg = (f"# {g[4]} ({g[5]})\n{g[3]}\n{add_msg}")
        await bot_msg(ctx, msg)

    @bot.tree.command(name="가디언예측", description="특정 날짜 가디언 예측하기")
    @app_commands.describe(
        year="년 (예: 2026)",
        month="월 (예: 3)",
        day="일 (예: 5)"
    )
    async def predict_guardian(ctx, year: int, month: int, day: int):
        bot.add_log(ctx, "/가디언예측", f"{year}-{month}-{day}")
        g = LostArkGuardian().get_lostark_weekly_info_predict(year, month, day)
        
        msg = (f"""# {g[1]} ({g[2]})\n{g[0]}""")
        await bot_msg(ctx, msg)



    @bot.hybrid_command(name="쌀", description="경매 쌀산기")
    @app_commands.describe(
        거래소="경매템 가격",
        컨텐츠인원="몇인팟 컨텐츠임?"
    )
    async def calculate(ctx, 거래소: int, 컨텐츠인원: int):
        logic_response = calc_logic(거래소, 컨텐츠인원)
        
        response_text = logic_response[0]
        response_tuple = logic_response[1]
        
        if type(response_tuple) == tuple:
            bot.add_log(ctx,
                    "/쌀",
                    f"가격: {거래소}, 인원수: {컨텐츠인원}, 추천입찰가: {response_tuple[1]:,}G, 분배금: {response_tuple[2]:,}G, 판매금: {response_tuple[3]:,}G")
            # interaction.response.send_message를 통해 답장을 보냅니다.
            await bot_msg(ctx, response_text)
        else:
            bot.add_log(ctx,
                        "/쌀",
                        f"가격: {거래소}, 인원수: {컨텐츠인원}, 응답: {logic_response}"
                        )
            await bot_msg(ctx, logic_response) # type: ignore


    @bot.hybrid_command(name="선점쌀", description="경매 쌀산기 (선점가)")
    @app_commands.describe(
        거래소="경매템 가격",
        컨텐츠인원="몇인팟 컨텐츠임?"
    )
    async def calculate_v2(ctx, 거래소: int, 컨텐츠인원: int):
        logic_response = calc_logic_v2(거래소, 컨텐츠인원)
        
        response_text = logic_response[0]
        response_tuple = logic_response[1]
        
        if type(response_tuple) == tuple:
            bot.add_log(ctx,
                    "/쌀",
                    f"가격: {거래소}, 인원수: {컨텐츠인원}, 추천입찰가: {response_tuple[1]:,}G, 분배금: {response_tuple[2]:,}G, 판매금: {response_tuple[3]:,}G")
            # interaction.response.send_message를 통해 답장을 보냅니다.
            await bot_msg(ctx, response_text)
        else:
            bot.add_log(ctx,
                        "/쌀",
                        f"가격: {거래소}, 인원수: {컨텐츠인원}, 응답: {logic_response}"
                        )
            await bot_msg(ctx, logic_response) # type: ignore  