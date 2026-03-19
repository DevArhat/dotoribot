import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import os

from logic import SpaceController

sc = SpaceController()
load_dotenv()
KAKAO_MAP_API_KEY = f"KakaoAK {os.getenv('KAKAO_MAP_API_KEY')}"
REQ_URL = "https://dapi.kakao.com/v2/local/search/keyword.json?"

ITEMS_PER_PAGE = 4
TOTAL_PAGES = 15


class KakaoMapPaginationView(discord.ui.View):
    """카카오맵 검색 결과 페이지네이션 View"""

    def __init__(self, pages, 동네, total_count):
        super().__init__(timeout=None)
        self.pages = pages          # list of list[dict]
        self.동네 = 동네
        self.total_count = total_count
        self.current_page = 0
        self._update_buttons()

    def _update_buttons(self):
        self.first_button.disabled = self.current_page == 0
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= len(self.pages) - 1
        self.last_button.disabled = self.current_page >= len(self.pages) - 1
        self.page_indicator.label = f"{self.current_page + 1} / {len(self.pages)}"

    def _build_embed(self):
        page_data = self.pages[self.current_page]
        descriptions = []
        for place in page_data:
            name = place.get('place_name', '이름 없음')
            url = place.get('place_url', '#')
            category = place.get('category_name', '정보 없음')
            address = place.get('road_address_name') or place.get('address_name')
            phone = place.get('phone', '번호 없음')

            item_str = (
                f"### [{name}]({url})\n"
                f"분류 : {category}\n"
                f"위치 : {address}\n"
                f"전화 : {phone}\n"
            )
            descriptions.append(item_str)

        embed = discord.Embed(
            title=f"{self.동네} 검색결과",
            description="\n".join(descriptions),
            color=discord.Color.green()
        )
        embed.set_footer(
            text=f"Powered by Kakao Maps · 총 {self.total_count}개 결과 · 페이지 {self.current_page + 1}/{len(self.pages)}",
            icon_url="https://t1.kakaocdn.net/kakaocorp/corp_nw/logo.png"
        )
        return embed

    @discord.ui.button(label="⏪", style=discord.ButtonStyle.secondary)
    async def first_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 0
        self._update_buttons()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    @discord.ui.button(label="1 / 1", style=discord.ButtonStyle.secondary, disabled=True)
    async def page_indicator(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass  # 페이지 표시용 버튼, 상호작용 없음

    @discord.ui.button(label="▶", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(len(self.pages) - 1, self.current_page + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    @discord.ui.button(label="⏩", style=discord.ButtonStyle.secondary)
    async def last_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = len(self.pages) - 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


def kakao_map_utils_commands(bot, bot_msg, bot_defer):
    @bot.hybrid_command(name="식당")
    @commands.cooldown(1, 60, commands.BucketType.user)
    @app_commands.describe(
        동네="검색할 동네"
    )
    async def search_kakao_map(ctx, 동네: str = '서울'):
        search_key = sc.remove_space(동네)
        await bot_defer(ctx, defer_msg=f"🐿️ {동네.strip()} 돌아다녀보고 올게요!")
        headers = {
            "Authorization": KAKAO_MAP_API_KEY
        }

        # 카카오 API에서 최대 size=15, page 1~4 로 최대 60개 결과를 가져옴
        # 그 중 ITEMS_PER_PAGE * TOTAL_PAGES = 60개까지 사용
        all_documents = []
        max_needed = ITEMS_PER_PAGE * TOTAL_PAGES  # 60

        for page_num in range(1, 5):  # page 1, 2, 3, 4
            if len(all_documents) >= max_needed:
                break

            params = {
                "query": f"{search_key}",
                "category_group_code": "FD6",
                "sort": "accuracy",
                "size": 15,
                "page": page_num
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(REQ_URL, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        documents = data.get('documents', [])
                        all_documents.extend(documents)

                        # API가 마지막 페이지인지 확인
                        meta = data.get('meta', {})
                        if meta.get('is_end', True):
                            break
                    else:
                        if not all_documents:
                            bot.add_log(ctx, "/식당", f"{동네}, 응답:{response.status}")
                            return await bot_msg(ctx, "😉 못찾았어!")
                        break

        if not all_documents:
            bot.add_log(ctx, "/식당", f"{동네}, 결과없음")
            return await bot_msg(ctx, "😉 못찾았어!")

        # max_needed 개까지만 사용
        all_documents = all_documents[:max_needed]

        # ITEMS_PER_PAGE 단위로 페이지 분할
        pages = []
        for i in range(0, len(all_documents), ITEMS_PER_PAGE):
            pages.append(all_documents[i:i + ITEMS_PER_PAGE])

        total_count = len(all_documents)

        view = KakaoMapPaginationView(pages, 동네, total_count)
        embed = view._build_embed()

        bot.add_log(ctx, "/식당", f"{동네}, {total_count}개 결과, {len(pages)}페이지")

        # interaction 기반으로 view 전송
        inter = ctx if isinstance(ctx, discord.Interaction) else getattr(ctx, 'interaction', None)
        if inter:
            await inter.edit_original_response(content="# 밥먹자 :yum:", embed=embed, view=view)
        else:
            await ctx.send(content="# 밥먹자 :yum:", embed=embed, view=view)

    @search_kakao_map.error
    async def kakao_map_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            # 쿨타임 중일 때 bot_msg 호출
            await bot_msg(ctx, content=f"🤫 아직 식당을 찾을 수 없어요! {error.retry_after:.1f}초 후에 다시 시도해주세요.", ephemeral=True)
        else:
            # 기타 에러는 상위 핸들러가 처리하도록 다시 발생
            raise error
