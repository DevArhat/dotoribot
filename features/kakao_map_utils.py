import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp
from dotenv import load_dotenv

from logic import SpaceController

sc = SpaceController()
load_dotenv()
KAKAO_MAP_API_KEY = f"KakaoAK {os.getenv('KAKAO_MAP_API_KEY')}"
REQ_URL = "https://dapi.kakao.com/v2/local/search/keyword.json?"

def kakao_map_utils_commands(bot, bot_msg, bot_defer):
    @bot.hybrid_command(name="식당")
    @app_commands.describe(
        동네="검색할 동네"
    )
    async def kakao_map(ctx, 동네: str = '서울'):
        await bot_defer(ctx)
        headers = {
            "Authorization": KAKAO_MAP_API_KEY
        }
        print(headers)
        params = {
            "query": f"{동네}",
            "category_group_code": "FD6",
            "sort": "accuracy",
            "size": 10
        }
        reponse_status = None
        async with aiohttp.ClientSession() as session:
            async with session.get(REQ_URL, headers=headers, params=params) as response:
                if response.status == 200:
                    reponse_status = 200
                    data = await response.json()
                else:
                    reponse_status = response.status
                    data = None
        if not data:
            bot.add_log(ctx, "/식당", f"{동네}, 응답:{reponse_status}")
            return await bot_msg(ctx, "😉 못찾았어!")

        parsed_data = data.get('documents', None)

        result_text = ''
        if not parsed_data:
            result_text = "검색 결과가 없습니다."

        descriptions = []
        for place in parsed_data:
            name = place.get('place_name', '이름 없음')
            url = place.get('place_url', '#')
            category = place.get('category_name', '정보 없음')
            address = place.get('road_address_name') or place.get('address_name')
            phone = place.get('phone', '번호 없음')

            # 요청하신 포맷 적용
            item_str = (
            f"### [{name}]({url})\n"
            f"분류 : {category}\n"
            f"위치 : {address}\n"
            f"전화 : {phone}\n"
        )
            descriptions.append(item_str)

        
        embed = discord.Embed(title=f"{동네} 검색결과", description=result_text, color=discord.Color.green())
        embed.description = "\n".join(descriptions)
        embed.set_footer(text="Powered by Kakao Maps", icon_url="https://t1.kakaocdn.net/kakaocorp/corp_nw/logo.png")

        bot.add_log(ctx, "/식당", f"{동네}")
        await bot_msg(ctx,content="# 밥먹자 :yum:", embed=embed)
